# Databricks notebook source
"""Registers a retry-safe Sprint 1 source snapshot before Bronze ingestion.

Requested artifact: notebook_02_snapshot_registration.
The deployed job path remains ``90_register_source_snapshot``.
"""

from datetime import datetime, timezone
import json
import logging
import uuid

from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql import types as T


def _get(name: str, default=None):
    try:
        widgets = dbutils.widgets  # type: ignore[name-defined]
    except NameError:
        value = default
    else:
        value = widgets.get(name)
    return value.strip() if isinstance(value, str) and value.strip() else default


def _required(name: str) -> str:
    value = _get(name)
    if not value:
        raise ValueError("Required parameter is missing: %s" % name)
    return value


def _logger() -> logging.Logger:
    logger = logging.getLogger("offball.sprint1.snapshot_registration")
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    return logger


def _snapshot_schema() -> T.StructType:
    return T.StructType(
        [
            T.StructField("delivery_key", T.StringType(), False),
            T.StructField("source_snapshot_id", T.StringType(), False),
            T.StructField("ingestion_attempt_id", T.StringType(), False),
            T.StructField("source_system_code", T.StringType(), False),
            T.StructField("source_object_name", T.StringType(), False),
            T.StructField("source_version", T.StringType(), False),
            T.StructField("captured_at", T.TimestampType(), False),
            T.StructField("object_uri", T.StringType(), True),
            T.StructField("source_domain", T.StringType(), True),
            T.StructField("run_mode", T.StringType(), False),
            T.StructField("expected_record_count", T.LongType(), True),
            T.StructField("actual_record_count", T.LongType(), True),
            T.StructField("accepted_count", T.LongType(), True),
            T.StructField("rejected_count", T.LongType(), True),
            T.StructField("quarantined_count", T.LongType(), True),
            T.StructField("duplicate_count", T.LongType(), True),
            T.StructField("snapshot_status", T.StringType(), False),
            T.StructField("created_at", T.TimestampType(), False),
            T.StructField("finalized_at", T.TimestampType(), True),
        ]
    )


def _ensure_snapshot_table(table_name: str) -> None:
    if not spark.catalog.tableExists(table_name):  # type: ignore[name-defined]
        spark.createDataFrame([], _snapshot_schema()).write.format("delta").mode(
            "overwrite"
        ).saveAsTable(table_name)
        return

    existing = {field.name for field in spark.table(table_name).schema}  # type: ignore[name-defined]
    additions = [
        field
        for field in _snapshot_schema().fields
        if field.name not in existing
    ]
    if additions:
        definitions = ", ".join(
            "`%s` %s" % (field.name, field.dataType.simpleString())
            for field in additions
        )
        quoted_table = ".".join("`%s`" % part for part in table_name.split("."))
        spark.sql("ALTER TABLE %s ADD COLUMNS (%s)" % (quoted_table, definitions))


def _publish_task_value(key: str, value: str) -> None:
    try:
        dbutils.jobs.taskValues.set(key=key, value=value)  # type: ignore[name-defined]
    except Exception as exc:
        raise RuntimeError(
            "Unable to publish required task value %s" % key
        ) from exc


def main() -> None:
    logger = _logger()
    catalog = _required("catalog")
    bronze_schema = _get("bronze_schema", "bronze")
    source_system_code = _required("source_system_code")
    source_object_name = _required("source_object_name")
    source_version = _required("source_version")
    bronze_root_uri = _required("bronze_root_uri")
    source_delivery_uri = _required("source_delivery_uri")
    if source_system_code == "configured-provider":
        raise ValueError("source_system_code must identify a configured provider")
    source_domain = _get("source_domain")
    run_mode = _get("run_mode", "incremental")
    expected_value = _get("expected_record_count")
    expected_count = int(expected_value) if expected_value else None
    if run_mode not in {"batch", "incremental", "replay"}:
        raise ValueError("run_mode must be batch, incremental, or replay")

    replay_id = _get("replay_id")
    if run_mode == "replay" and not replay_id:
        raise ValueError("replay_id is required when run_mode is replay")

    delivery_key = "|".join(
        [
            source_system_code,
            source_object_name,
            source_version,
            source_delivery_uri,
            source_domain or "",
            run_mode,
            replay_id or "",
        ]
    )
    namespace = uuid.NAMESPACE_URL
    snapshot_id = str(uuid.uuid5(namespace, "snapshot|" + delivery_key))
    attempt_id = str(uuid.uuid5(namespace, "attempt|" + delivery_key))
    now = datetime.now(timezone.utc)
    table_name = "%s.%s._source_snapshot" % (catalog, bronze_schema)
    _ensure_snapshot_table(table_name)

    row = [
        (
            delivery_key,
            snapshot_id,
            attempt_id,
            source_system_code,
            source_object_name,
            source_version,
            now,
            source_delivery_uri,
            source_domain,
            run_mode,
            expected_count,
            None,
            None,
            None,
            None,
            None,
            "registered",
            now,
            None,
        )
    ]
    incoming = spark.createDataFrame(row, _snapshot_schema())  # type: ignore[name-defined]
    target = DeltaTable.forName(spark, table_name)  # type: ignore[name-defined]
    (
        target.alias("target")
        .merge(
            incoming.alias("source"),
            "target.`delivery_key` <=> source.`delivery_key`",
        )
        .whenMatchedUpdate(
            condition=(
                "target.`snapshot_status` NOT IN "
                "('completed', 'completed_with_quarantine', 'failed') "
                "OR source.`run_mode` = 'replay'"
            ),
            set={
                "source_snapshot_id": "source.source_snapshot_id",
                "ingestion_attempt_id": "source.ingestion_attempt_id",
                "captured_at": "source.captured_at",
                "object_uri": "source.object_uri",
                "expected_record_count": "source.expected_record_count",
                "snapshot_status": "source.snapshot_status",
            }
        )
        .whenNotMatchedInsertAll()
        .execute()
    )

    registered = (
        spark.table(table_name)  # type: ignore[name-defined]
        .where(F.col("delivery_key") == F.lit(delivery_key))
        .select("source_snapshot_id", "ingestion_attempt_id")
        .limit(1)
        .collect()
    )
    if len(registered) != 1:
        raise RuntimeError(
            "Snapshot registration did not produce exactly one delivery record"
        )
    snapshot_id = registered[0]["source_snapshot_id"]
    attempt_id = registered[0]["ingestion_attempt_id"]
    _publish_task_value("source_snapshot_id", snapshot_id)
    _publish_task_value("ingestion_attempt_id", attempt_id)
    logger.info(
        "Registered source snapshot id=%s ingestion_attempt_id=%s source=%s object=%s version=%s",
        snapshot_id,
        attempt_id,
        source_system_code,
        source_object_name,
        source_version,
    )
    print(
        json.dumps(
            {
                "source_snapshot_id": snapshot_id,
                "ingestion_attempt_id": attempt_id,
                "status": "registered",
            }
        )
    )


if __name__ == "__main__":
    main()
