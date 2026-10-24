# Databricks notebook source
"""Reusable Bronze ingestion helpers for Sprint 1."""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, Iterable, Optional, Sequence

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql import types as T
from delta.tables import DeltaTable


COMMON_BRONZE_SCHEMA = T.StructType(
    [
        T.StructField("ingestion_id", T.StringType(), False),
        T.StructField("source_snapshot_id", T.StringType(), False),
        T.StructField("ingestion_attempt_id", T.StringType(), False),
        T.StructField("source_system_code", T.StringType(), False),
        T.StructField("source_record_reference", T.StringType(), True),
        T.StructField("source_object_name", T.StringType(), False),
        T.StructField("source_version", T.StringType(), False),
        T.StructField("payload_json", T.StringType(), False),
        T.StructField("payload_hash", T.StringType(), False),
        T.StructField("source_event_timestamp", T.TimestampType(), True),
        T.StructField("ingested_at", T.TimestampType(), False),
        T.StructField("file_uri", T.StringType(), True),
        T.StructField("rescued_data", T.StringType(), True),
        T.StructField("ingestion_status", T.StringType(), False),
    ]
)


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def payload_hash(payload_json: str) -> str:
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()


def build_ingestion_id(source_system_code: str, source_object_name: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    digest = hashlib.sha256(
        ("%s|%s|%s" % (source_system_code, source_object_name, timestamp)).encode(
            "utf-8"
        )
    ).hexdigest()[:16]
    return "%s-%s" % (timestamp, digest)


def require_metadata(
    source_system_code: Optional[str],
    source_object_name: Optional[str],
    source_version: Optional[str],
) -> None:
    missing = [
        name
        for name, value in (
            ("source_system_code", source_system_code),
            ("source_object_name", source_object_name),
            ("source_version", source_version),
        )
        if not value
    ]
    if missing:
        raise ValueError("Missing required source metadata: %s" % ", ".join(missing))
    if source_system_code == "configured-provider":
        raise ValueError("source_system_code must identify a configured provider")


def add_common_columns(
    dataframe: DataFrame,
    ingestion_id: str,
    source_snapshot_id: str,
    ingestion_attempt_id: str,
    source_system_code: str,
    source_object_name: str,
    source_version: str,
    file_uri: Optional[str] = None,
    source_record_reference_column: Optional[str] = None,
    source_event_timestamp_column: Optional[str] = None,
) -> DataFrame:
    """Adds the immutable Bronze contract without dropping source columns."""
    payload_columns = [
        F.col(column)
        for column in dataframe.columns
        if column
        not in {
            "ingestion_id",
            "source_snapshot_id",
            "ingestion_attempt_id",
            "source_system_code",
            "source_record_reference",
            "source_object_name",
            "source_version",
            "payload_json",
            "payload_hash",
            "source_event_timestamp",
            "ingested_at",
            "file_uri",
            "rescued_data",
            "ingestion_status",
        }
    ]
    payload_json = F.to_json(F.struct(*payload_columns))
    if source_record_reference_column and source_record_reference_column in dataframe.columns:
        source_reference = F.col(source_record_reference_column).cast("string")
    else:
        source_reference = F.lit(None).cast("string")
    if source_event_timestamp_column and source_event_timestamp_column in dataframe.columns:
        source_timestamp = F.to_timestamp(F.col(source_event_timestamp_column))
    else:
        source_timestamp = F.lit(None).cast("timestamp")
    return (
        dataframe.withColumn("ingestion_id", F.lit(ingestion_id))
        .withColumn("source_snapshot_id", F.lit(source_snapshot_id))
        .withColumn("ingestion_attempt_id", F.lit(ingestion_attempt_id))
        .withColumn("source_system_code", F.lit(source_system_code))
        .withColumn("source_record_reference", source_reference)
        .withColumn("source_object_name", F.lit(source_object_name))
        .withColumn("source_version", F.lit(source_version))
        .withColumn("payload_json", payload_json)
        .withColumn("payload_hash", F.sha2(F.col("payload_json"), 256))
        .withColumn("source_event_timestamp", source_timestamp)
        .withColumn("ingested_at", F.current_timestamp())
        .withColumn("file_uri", F.lit(file_uri).cast("string"))
        .withColumn("rescued_data", F.lit(None).cast("string"))
        .withColumn("ingestion_status", F.lit("accepted"))
    )


def ensure_bronze_table(
    dataframe: DataFrame,
    table_name: str,
    partition_columns: Iterable[str],
) -> None:
    """Creates a Delta table from the first valid batch and never enables auto-merge."""
    missing_partition_columns = [
        column for column in partition_columns if column not in dataframe.columns
    ]
    for column in missing_partition_columns:
        dataframe = dataframe.withColumn(column, F.lit(None).cast("string"))
    (
        dataframe.write.format("delta")
        .mode("append")
        .partitionBy(*list(partition_columns))
        .option("mergeSchema", "false")
        .saveAsTable(table_name)
    )


def ensure_bronze_columns(table_name: str, columns: Sequence[str]) -> None:
    """Adds required operational columns to an existing Bronze Delta table."""
    existing = {field.name for field in spark.table(table_name).schema}  # type: ignore[name-defined]
    additions = [
        column
        for column in columns
        if column not in existing
    ]
    if additions:
        definitions = ", ".join("`%s` STRING" % column for column in additions)
        quoted_table = ".".join("`%s`" % part for part in table_name.split("."))
        spark.sql("ALTER TABLE %s ADD COLUMNS (%s)" % (quoted_table, definitions))  # type: ignore[name-defined]


def write_bronze_idempotent(
    dataframe: DataFrame,
    table_name: str,
    key_columns: Iterable[str],
    partition_columns: Iterable[str],
) -> Dict[str, int]:
    """Appends only unseen source records, keyed by source identity and payload hash."""
    keys = list(key_columns)
    if not keys:
        raise ValueError("At least one idempotency key is required")
    if spark.catalog.tableExists(table_name):  # type: ignore[name-defined]
        existing = spark.table(table_name).select(*keys).dropDuplicates(keys)  # type: ignore[name-defined]
        new_rows = dataframe.join(existing, keys, "left_anti")
    else:
        new_rows = dataframe
    accepted_count = new_rows.count()
    if accepted_count:
        ensure_bronze_table(new_rows, table_name, partition_columns)
    return {"accepted_count": accepted_count}


def read_source(
    source_path: str,
    source_format: str,
    source_schema: T.StructType,
    options: Optional[Dict[str, str]] = None,
) -> DataFrame:
    """Reads a bounded delivery using an explicit source contract."""
    normalized_format = source_format.lower()
    if normalized_format not in {"json", "csv", "parquet", "delta"}:
        raise ValueError(
            "Unsupported source_format=%s; expected json, csv, parquet, or delta"
            % source_format
        )
    reader = spark.read.format(normalized_format).schema(source_schema)  # type: ignore[name-defined]
    for key, value in (options or {}).items():
        reader = reader.option(key, value)
    return reader.load(source_path)


def _read_contract_text(path: str) -> str:
    try:
        return dbutils.fs.head(path, 10 * 1024 * 1024)  # type: ignore[name-defined]
    except NameError as exc:
        raise RuntimeError(
            "Schema registry access requires a Databricks runtime: %s" % path
        ) from exc
    except Exception as exc:
        raise RuntimeError("Unable to read source schema contract: %s" % path) from exc


def load_source_contract(
    schema_registry_root_uri: str,
    source_object_name: str,
    source_version: str,
) -> Dict[str, Any]:
    if not schema_registry_root_uri:
        raise ValueError("schema_registry_root_uri is required")
    path = "%s/%s/%s.json" % (
        schema_registry_root_uri.rstrip("/"),
        source_object_name,
        source_version,
    )
    try:
        contract = json.loads(_read_contract_text(path))
    except json.JSONDecodeError as exc:
        raise ValueError("Schema contract is not valid JSON: %s" % path) from exc
    if contract.get("source_object_name") != source_object_name:
        raise ValueError("Schema contract source object mismatch: %s" % path)
    if str(contract.get("source_version")) != str(source_version):
        raise ValueError("Schema contract source version mismatch: %s" % path)
    schema_json = contract.get("schema")
    if not schema_json:
        raise ValueError("Schema contract has no schema: %s" % path)
    try:
        source_schema = T.StructType.fromJson(schema_json)
    except (TypeError, KeyError, ValueError) as exc:
        raise ValueError("Schema contract has invalid Spark schema: %s" % path) from exc
    contract["source_schema"] = source_schema
    contract["contract_path"] = path
    return contract


def validate_source_contract(
    dataframe: DataFrame,
    contract: Dict[str, Any],
    required_column_groups: Sequence[Sequence[str]],
) -> DataFrame:
    available = set(dataframe.columns)
    configured_groups = contract.get("required_column_groups", required_column_groups)
    missing_groups = [
        list(group)
        for group in configured_groups
        if not any(column in available for column in group)
    ]
    if missing_groups:
        raise ValueError(
            "Source contract is missing required column groups: %s"
            % json.dumps(missing_groups, sort_keys=True)
        )
    return dataframe


def _source_read_options(
    source_format: str,
    options: Optional[Dict[str, str]],
) -> Dict[str, str]:
    read_options = dict(options or {})
    if source_format.lower() == "csv":
        read_options.setdefault("header", "true")
    return read_options


def merge_bronze_idempotent(
    dataframe: DataFrame,
    table_name: str,
    key_columns: Sequence[str],
    partition_columns: Sequence[str],
) -> Dict[str, int]:
    """Merges source identity plus payload hash and preserves immutable history."""
    keys = list(key_columns)
    if not keys:
        raise ValueError("At least one MERGE key is required")
    required_columns = set(keys).union(
        {"payload_hash", "source_snapshot_id", "ingestion_attempt_id"}
    )
    missing_columns = sorted(required_columns.difference(dataframe.columns))
    if missing_columns:
        raise ValueError(
            "Bronze MERGE is missing required columns: %s"
            % ", ".join(missing_columns)
        )
    for column in partition_columns:
        if column not in dataframe.columns:
            dataframe = dataframe.withColumn(column, F.lit(None).cast("string"))
    input_count = dataframe.count()
    incoming = dataframe.dropDuplicates(keys)
    candidate_count = incoming.count()
    in_batch_duplicate_count = input_count - candidate_count
    if spark.catalog.tableExists(table_name):  # type: ignore[name-defined]
        ensure_bronze_columns(
            table_name,
            ["source_snapshot_id", "ingestion_attempt_id"],
        )
        target = DeltaTable.forName(spark, table_name)  # type: ignore[name-defined]
        condition = " AND ".join(
            "target.`%s` <=> source.`%s`" % (key, key) for key in keys
        )
        existing_keys = spark.table(table_name).select(*keys).dropDuplicates(keys)  # type: ignore[name-defined]
        duplicate_condition = None
        for key in keys:
            expression = incoming[key].eqNullSafe(existing_keys[key])
            duplicate_condition = (
                expression
                if duplicate_condition is None
                else duplicate_condition & expression
            )
        duplicate_count = incoming.join(
            existing_keys,
            duplicate_condition,
            "leftsemi",
        ).count()
        (
            target.alias("target")
            .merge(incoming.alias("source"), condition)
            .whenNotMatchedInsertAll()
            .execute()
        )
        return {
            "candidate_count": candidate_count,
            "inserted_count": candidate_count - duplicate_count,
            "duplicate_count": duplicate_count + in_batch_duplicate_count,
        }
    ensure_bronze_table(incoming, table_name, partition_columns)
    return {
        "candidate_count": candidate_count,
        "inserted_count": candidate_count,
        "duplicate_count": in_batch_duplicate_count,
    }


def _required_task_value(task_key: str, key: str) -> str:
    try:
        value = dbutils.jobs.taskValues.get(  # type: ignore[name-defined]
            taskKey=task_key,
            key=key,
            default="",
            debugValue="",
        )
    except NameError as exc:
        raise RuntimeError(
            "Required Databricks task value is unavailable outside a Databricks job: %s"
            % key
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            "Unable to read required Databricks task value %s from %s"
            % (key, task_key)
        ) from exc
    if not value:
        raise RuntimeError(
            "Required Databricks task value is empty: %s from %s" % (key, task_key)
        )
    return str(value)


def publish_ingestion_metrics(result: Dict[str, Any]) -> None:
    for key in (
        "candidate_count",
        "inserted_count",
        "duplicate_count",
        "quarantined_count",
    ):
        try:
            dbutils.jobs.taskValues.set(  # type: ignore[name-defined]
                key=key,
                value=str(int(result.get(key, 0))),
            )
        except NameError as exc:
            raise RuntimeError(
                "Ingestion metrics require a Databricks job runtime"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                "Unable to publish ingestion metric: %s" % key
            ) from exc


def ingest_source_to_bronze(
    config,
    source_path: str,
    source_format: str,
    table: str,
    source_system_code: str,
    source_object_name: str,
    source_version: str,
    source_record_reference_candidates: Sequence[str],
    source_event_timestamp_candidates: Sequence[str],
    partition_columns: Sequence[str],
    required_column_groups: Sequence[Sequence[str]],
    read_options: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Executes one complete Bronze ingestion with quarantine and MERGE semantics."""
    require_metadata(source_system_code, source_object_name, source_version)
    if not source_path:
        raise ValueError("source_path is required")
    registered_snapshot_id = _required_task_value(
        "register_snapshot", "source_snapshot_id"
    )
    registered_attempt_id = _required_task_value(
        "register_snapshot", "ingestion_attempt_id"
    )
    if config.snapshot_id and config.snapshot_id != registered_snapshot_id:
        raise ValueError("snapshot_id does not match the registered task value")
    if config.ingestion_id and config.ingestion_id != registered_attempt_id:
        raise ValueError("ingestion_id does not match the registered task value")
    ingestion_id = registered_attempt_id
    LOGGER.info(
        "Using registered snapshot=%s ingestion_attempt=%s",
        registered_snapshot_id,
        registered_attempt_id,
    )
    contract = load_source_contract(
        config.schema_registry_root_uri,
        source_object_name,
        source_version,
    )
    source_schema = contract["source_schema"]
    read_options = _source_read_options(source_format, read_options)
    totals = {
        "candidate_count": 0,
        "inserted_count": 0,
        "duplicate_count": 0,
        "quarantined_count": 0,
    }

    def process_batch(raw: DataFrame) -> None:
        if not raw.columns:
            raise ValueError("Source delivery contains no columns: %s" % source_path)
        validate_source_contract(raw, contract, required_column_groups)
        reference = next(
            (column for column in source_record_reference_candidates if column in raw.columns),
            None,
        )
        timestamp = next(
            (column for column in source_event_timestamp_candidates if column in raw.columns),
            None,
        )
        enriched = add_common_columns(
            raw,
            ingestion_id=ingestion_id,
            source_snapshot_id=registered_snapshot_id,
            ingestion_attempt_id=registered_attempt_id,
            source_system_code=source_system_code,
            source_object_name=source_object_name,
            source_version=source_version,
            file_uri=source_path,
            source_record_reference_column=reference,
            source_event_timestamp_column=timestamp,
        ).withColumn("ingestion_date", F.to_date("ingested_at"))
        required_metadata = [
            "ingestion_id",
            "source_snapshot_id",
            "ingestion_attempt_id",
            "source_system_code",
            "source_object_name",
            "source_version",
            "payload_json",
            "payload_hash",
            "ingested_at",
            "ingestion_status",
        ]
        invalid = None
        for column in required_metadata:
            condition = F.col(column).isNull()
            invalid = condition if invalid is None else invalid | condition
        if reference:
            invalid = invalid | F.col("source_record_reference").isNull()
        invalid_rows = enriched.where(invalid)
        valid_rows = enriched.where(~invalid)
        quarantine_count = write_quarantine(
            invalid_rows,
            "%s/%s" % (config.quarantine_root_uri.rstrip("/"), table),
            "required Bronze metadata is missing",
        )
        merge_keys = ["source_system_code", "source_record_reference", "payload_hash"]
        if not reference:
            merge_keys = ["source_system_code", "source_object_name", "payload_hash"]
        result = merge_bronze_idempotent(
            valid_rows,
            config.table_name(table),
            merge_keys,
            partition_columns,
        )
        for key in ("candidate_count", "inserted_count", "duplicate_count"):
            totals[key] += result.get(key, 0)
        totals["quarantined_count"] += quarantine_count

    if config.run_mode == "incremental":
        if not config.checkpoint_root_uri:
            raise ValueError("checkpoint_root_uri is required for incremental mode")
        stream = (
            spark.readStream.format("cloudFiles")  # type: ignore[name-defined]
            .option("cloudFiles.format", source_format.lower())
            .option(
                "cloudFiles.schemaLocation",
                "%s/%s" % (config.schema_registry_root_uri.rstrip("/"), source_object_name),
            )
            .schema(source_schema)
        )
        for key, value in read_options.items():
            stream = stream.option(key, value)
        query = (
            stream.load(source_path)
            .writeStream.foreachBatch(lambda batch, _: process_batch(batch))
            .option(
                "checkpointLocation",
                "%s/%s" % (config.checkpoint_root_uri.rstrip("/"), source_object_name),
            )
            .trigger(availableNow=True)
            .start()
        )
        query.awaitTermination()
    else:
        raw = read_source(source_path, source_format, source_schema, read_options)
        process_batch(raw)
    totals.update(
        {
            "source_path": source_path,
            "ingestion_id": ingestion_id,
            "source_snapshot_id": registered_snapshot_id,
            "ingestion_attempt_id": registered_attempt_id,
            "contract_path": contract["contract_path"],
        }
    )
    return totals


def write_quarantine(
    dataframe: DataFrame,
    quarantine_path: str,
    rejection_reason: str,
) -> int:
    if dataframe.rdd.isEmpty():
        return 0
    quarantined = (
        dataframe.withColumn("ingestion_status", F.lit("quarantined"))
        .withColumn("rejection_reason", F.lit(rejection_reason))
        .withColumn("quarantined_at", F.current_timestamp())
    )
    key_columns = [
        "source_snapshot_id",
        "ingestion_attempt_id",
        "source_system_code",
        "source_object_name",
        "source_record_reference",
        "payload_hash",
        "rejection_reason",
    ]
    missing_keys = sorted(set(key_columns).difference(quarantined.columns))
    if missing_keys:
        raise ValueError(
            "Quarantine data is missing idempotency columns: %s"
            % ", ".join(missing_keys)
        )
    quarantined = quarantined.dropDuplicates(key_columns)
    candidate_count = quarantined.count()
    if not DeltaTable.isDeltaTable(spark, quarantine_path):  # type: ignore[name-defined]
        quarantined.write.format("delta").mode("append").save(quarantine_path)
        return candidate_count

    target = DeltaTable.forPath(spark, quarantine_path)  # type: ignore[name-defined]
    existing_columns = set(
        field.name for field in spark.read.format("delta").load(quarantine_path).schema  # type: ignore[name-defined]
    )
    missing_columns = [
        field for field in quarantined.schema.fields if field.name not in existing_columns
    ]
    if missing_columns:
        definitions = ", ".join(
            "`%s` %s" % (field.name, field.dataType.simpleString())
            for field in missing_columns
        )
        spark.sql(
            "ALTER TABLE delta.`%s` ADD COLUMNS (%s)"
            % (quarantine_path.replace("`", "``"), definitions)
        )
    condition = " AND ".join(
        "target.`%s` <=> source.`%s`" % (key, key) for key in key_columns
    )
    existing_keys = (
        spark.read.format("delta")  # type: ignore[name-defined]
        .load(quarantine_path)
        .select(*key_columns)
        .dropDuplicates(key_columns)
    )
    join_condition = None
    for key in key_columns:
        expression = quarantined[key].eqNullSafe(existing_keys[key])
        join_condition = (
            expression
            if join_condition is None
            else join_condition & expression
        )
    new_count = quarantined.join(
        existing_keys,
        join_condition,
        "leftanti",
    ).count()
    (
        target.alias("target")
        .merge(quarantined.alias("source"), condition)
        .whenNotMatchedInsertAll()
        .execute()
    )
    return new_count
