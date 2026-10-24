# Databricks notebook source
"""Finalizes a retry-safe, source-snapshot-scoped Bronze ingestion attempt.

Requested artifact: notebook_03_snapshot_finalization.
The deployed job path remains ``91_finalize_ingestion_attempt``.
"""

from datetime import datetime, timezone
import json
import logging

from delta.tables import DeltaTable
from pyspark.sql import functions as F
from pyspark.sql import types as T


DOMAIN_TABLES = {
    "athlete": [
        "athlete_profile_raw",
        "roster_raw",
        "performance_stat_raw",
        "contract_raw",
        "eligibility_status_raw",
    ],
    "event": [
        "fixture_raw",
        "competition_raw",
        "participant_raw",
        "match_result_raw",
        "scoring_event_raw",
        "event_incident_raw",
    ],
    "tracking": ["tracking_frame_raw", "tracking_quality_raw"],
    "evidence_annotation": [
        "video_evidence_raw",
        "scouting_annotation_raw",
    ],
}

DOMAIN_TASKS = {
    "athlete": [
        "ingest_athlete_profile",
        "ingest_roster",
        "ingest_performance_stat",
        "ingest_contract",
        "ingest_eligibility_status",
    ],
    "event": [
        "ingest_fixture",
        "ingest_competition",
        "ingest_participant",
        "ingest_match_result",
        "ingest_scoring_event",
        "ingest_event_incident",
    ],
    "tracking": ["ingest_tracking_frame", "ingest_tracking_quality"],
    "evidence_annotation": [
        "ingest_video_evidence",
        "ingest_scouting_annotation",
    ],
}


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
            "Unable to read required task value %s from %s" % (key, task_key)
        ) from exc
    if not value:
        raise RuntimeError(
            "Required Databricks task value is empty: %s from %s" % (key, task_key)
        )
    return str(value)


def _publish_task_value(key: str, value: str) -> None:
    try:
        dbutils.jobs.taskValues.set(key=key, value=value)  # type: ignore[name-defined]
    except Exception as exc:
        raise RuntimeError(
            "Unable to publish required task value %s" % key
        ) from exc


def _task_metric(task_key: str, metric: str) -> int:
    try:
        value = dbutils.jobs.taskValues.get(  # type: ignore[name-defined]
            taskKey=task_key,
            key=metric,
            default="",
            debugValue="",
        )
    except NameError as exc:
        raise RuntimeError(
            "Task metrics require a Databricks job runtime"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            "Unable to read metric %s from task %s" % (metric, task_key)
        ) from exc
    if value in (None, ""):
        raise RuntimeError(
            "Missing required metric %s from task %s" % (metric, task_key)
        )
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "Metric %s from task %s is not an integer" % (metric, task_key)
        ) from exc


def _logger() -> logging.Logger:
    logger = logging.getLogger("offball.sprint1.snapshot_finalization")
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)
    return logger


def _attempt_schema() -> T.StructType:
    return T.StructType(
        [
            T.StructField("ingestion_attempt_id", T.StringType(), False),
            T.StructField("source_snapshot_id", T.StringType(), False),
            T.StructField("source_system_code", T.StringType(), False),
            T.StructField("source_object_name", T.StringType(), False),
            T.StructField("actual_record_count", T.LongType(), False),
            T.StructField("accepted_count", T.LongType(), False),
            T.StructField("rejected_count", T.LongType(), False),
            T.StructField("quarantined_count", T.LongType(), False),
            T.StructField("duplicate_count", T.LongType(), False),
            T.StructField("snapshot_status", T.StringType(), False),
            T.StructField("finalized_at", T.TimestampType(), False),
        ]
    )


def _ensure_attempt_table(table_name: str) -> None:
    if not spark.catalog.tableExists(table_name):  # type: ignore[name-defined]
        spark.createDataFrame([], _attempt_schema()).write.format("delta").mode(
            "overwrite"
        ).saveAsTable(table_name)
        return
    existing = {field.name for field in spark.table(table_name).schema}  # type: ignore[name-defined]
    additions = [
        field for field in _attempt_schema().fields if field.name not in existing
    ]
    if additions:
        definitions = ", ".join(
            "`%s` %s" % (field.name, field.dataType.simpleString())
            for field in additions
        )
        quoted_table = ".".join("`%s`" % part for part in table_name.split("."))
        spark.sql("ALTER TABLE %s ADD COLUMNS (%s)" % (quoted_table, definitions))


def _snapshot_row(table_name: str, snapshot_id: str):
    rows = (
        spark.table(table_name)  # type: ignore[name-defined]
        .where(F.col("source_snapshot_id") == F.lit(snapshot_id))
        .select(
            "source_system_code",
            "source_object_name",
            "source_domain",
        )
        .limit(1)
        .collect()
    )
    if len(rows) != 1:
        raise RuntimeError(
            "No unique registered snapshot found for source_snapshot_id=%s"
            % snapshot_id
        )
    return rows[0]


def _count_bronze_rows(
    catalog: str,
    bronze_schema: str,
    table_names,
    snapshot_id: str,
    attempt_id: str,
    status: str,
) -> int:
    total = 0
    for table in table_names:
        table_name = "%s.%s.%s" % (catalog, bronze_schema, table)
        if not spark.catalog.tableExists(table_name):  # type: ignore[name-defined]
            continue
        dataframe = spark.table(table_name)  # type: ignore[name-defined]
        required = {"source_snapshot_id", "ingestion_attempt_id", "ingestion_status"}
        missing = sorted(required.difference(dataframe.columns))
        if missing:
            raise RuntimeError(
                "Bronze table %s is missing required lineage columns: %s"
                % (table_name, ", ".join(missing))
            )
        total += (
            dataframe.where(
                (F.col("source_snapshot_id") == F.lit(snapshot_id))
                & (F.col("ingestion_attempt_id") == F.lit(attempt_id))
                & (F.col("ingestion_status") == F.lit(status))
            ).count()
        )
    return total


def _count_quarantine_rows(
    quarantine_root_uri: str,
    table_names,
    snapshot_id: str,
    attempt_id: str,
) -> int:
    total = 0
    for table in table_names:
        path = "%s/%s" % (quarantine_root_uri.rstrip("/"), table)
        if not DeltaTable.isDeltaTable(spark, path):  # type: ignore[name-defined]
            continue
        dataframe = spark.read.format("delta").load(path)  # type: ignore[name-defined]
        required = {"source_snapshot_id", "ingestion_attempt_id"}
        missing = sorted(required.difference(dataframe.columns))
        if missing:
            raise RuntimeError(
                "Quarantine path %s is missing required lineage columns: %s"
                % (path, ", ".join(missing))
            )
        total += (
            dataframe.where(
                (F.col("source_snapshot_id") == F.lit(snapshot_id))
                & (F.col("ingestion_attempt_id") == F.lit(attempt_id))
            )
            .select(
                "source_snapshot_id",
                "ingestion_attempt_id",
                "source_system_code",
                "source_object_name",
                "source_record_reference",
                "payload_hash",
                "rejection_reason",
            )
            .dropDuplicates()
            .count()
        )
    return total


def _update_snapshot_status(
    table_name: str,
    snapshot_id: str,
    status: str,
    counts,
    finalized_at,
) -> None:
    target = DeltaTable.forName(spark, table_name)  # type: ignore[name-defined]
    updates = {
        "snapshot_status": "source.snapshot_status",
        "actual_record_count": "source.actual_record_count",
        "accepted_count": "source.accepted_count",
        "rejected_count": "source.rejected_count",
        "quarantined_count": "source.quarantined_count",
        "duplicate_count": "source.duplicate_count",
        "finalized_at": "source.finalized_at",
    }
    source = spark.createDataFrame(  # type: ignore[name-defined]
        [
            (
                snapshot_id,
                status,
                counts["actual"],
                counts["accepted"],
                counts["rejected"],
                counts["quarantined"],
                counts["duplicate"],
                finalized_at,
            )
        ],
        T.StructType(
            [
                T.StructField("source_snapshot_id", T.StringType(), False),
                T.StructField("snapshot_status", T.StringType(), False),
                T.StructField("actual_record_count", T.LongType(), True),
                T.StructField("accepted_count", T.LongType(), True),
                T.StructField("rejected_count", T.LongType(), True),
                T.StructField("quarantined_count", T.LongType(), True),
                T.StructField("duplicate_count", T.LongType(), True),
                T.StructField("finalized_at", T.TimestampType(), True),
            ]
        ),
    )
    (
        target.alias("target")
        .merge(
            source.alias("source"),
            "target.`source_snapshot_id` <=> source.`source_snapshot_id`",
        )
        .whenMatchedUpdate(set=updates)
        .execute()
    )


def main() -> None:
    logger = _logger()
    catalog = _required("catalog")
    bronze_schema = _get("bronze_schema", "bronze")
    quarantine_root_uri = _required("quarantine_root_uri")
    registered_snapshot_id = _required_task_value(
        "register_snapshot", "source_snapshot_id"
    )
    registered_attempt_id = _required_task_value(
        "register_snapshot", "ingestion_attempt_id"
    )
    snapshot_id = _get("snapshot_id")
    attempt_id = _get("ingestion_attempt_id")
    if snapshot_id and snapshot_id != registered_snapshot_id:
        raise ValueError("snapshot_id does not match the registered task value")
    if attempt_id and attempt_id != registered_attempt_id:
        raise ValueError("ingestion_attempt_id does not match the registered task value")
    snapshot_id = registered_snapshot_id
    attempt_id = registered_attempt_id
    snapshot_table = "%s.%s._source_snapshot" % (catalog, bronze_schema)
    if not spark.catalog.tableExists(snapshot_table):  # type: ignore[name-defined]
        raise RuntimeError("Snapshot metadata table does not exist: %s" % snapshot_table)
    snapshot = _snapshot_row(snapshot_table, snapshot_id)
    source_domain = snapshot["source_domain"]
    table_names = DOMAIN_TABLES.get(source_domain)
    if not table_names:
        raise RuntimeError(
            "Registered snapshot has unsupported or missing source_domain: %s"
            % source_domain
        )

    accepted_count = _count_bronze_rows(
        catalog, bronze_schema, table_names, snapshot_id, attempt_id, "accepted"
    )
    rejected_count = _count_bronze_rows(
        catalog, bronze_schema, table_names, snapshot_id, attempt_id, "rejected"
    )
    quarantined_count = _count_quarantine_rows(
        quarantine_root_uri, table_names, snapshot_id, attempt_id
    )
    actual_count = accepted_count + rejected_count + quarantined_count
    duplicate_count = sum(
        _task_metric(task_key, "duplicate_count")
        for task_key in DOMAIN_TASKS[source_domain]
    )
    status = (
        "completed_with_quarantine"
        if quarantined_count > 0 or rejected_count > 0
        else "completed"
    )
    now = datetime.now(timezone.utc)
    counts = {
        "actual": actual_count,
        "accepted": accepted_count,
        "rejected": rejected_count,
        "quarantined": quarantined_count,
        "duplicate": duplicate_count,
    }

    attempt_table = "%s.%s._ingestion_attempt" % (catalog, bronze_schema)
    _ensure_attempt_table(attempt_table)
    row = [
        (
            attempt_id,
            snapshot_id,
            snapshot["source_system_code"],
            snapshot["source_object_name"],
            actual_count,
            accepted_count,
            rejected_count,
            quarantined_count,
            duplicate_count,
            status,
            now,
        )
    ]
    incoming = spark.createDataFrame(row, _attempt_schema())  # type: ignore[name-defined]
    target = DeltaTable.forName(spark, attempt_table)  # type: ignore[name-defined]
    (
        target.alias("target")
        .merge(
            incoming.alias("source"),
            "target.`ingestion_attempt_id` <=> source.`ingestion_attempt_id`",
        )
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
    _update_snapshot_status(snapshot_table, snapshot_id, status, counts, now)
    _publish_task_value("ingestion_attempt_id", attempt_id)
    _publish_task_value("snapshot_status", status)
    logger.info(
        "Finalized ingestion attempt id=%s snapshot=%s status=%s accepted=%s rejected=%s quarantined=%s",
        attempt_id,
        snapshot_id,
        status,
        accepted_count,
        rejected_count,
        quarantined_count,
    )
    print(
        json.dumps(
            {
                "ingestion_attempt_id": attempt_id,
                "snapshot_id": snapshot_id,
                "status": status,
                "actual_record_count": actual_count,
                "accepted_count": accepted_count,
                "rejected_count": rejected_count,
                "quarantined_count": quarantined_count,
                "duplicate_count": duplicate_count,
            }
        )
    )


if __name__ == "__main__":
    main()
