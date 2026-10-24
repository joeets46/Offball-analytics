# Databricks notebook source
"""Reusable deterministic Silver conformance helpers."""

from typing import Dict, Iterable, Optional, Sequence
import uuid
import logging

from delta.tables import DeltaTable
from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F
from pyspark.sql import types as T


LOGGER = logging.getLogger("offball.sprint2.silver")
if not LOGGER.handlers:
    LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.INFO)


def _exists(table_name: str) -> bool:
    return spark.catalog.tableExists(table_name)  # type: ignore[name-defined]


def source_rows(config, bronze_table: str) -> DataFrame:
    table_name = config.bronze_table(bronze_table)
    if not _exists(table_name):
        raise RuntimeError("Required Bronze table does not exist: %s" % table_name)
    dataframe = spark.table(table_name)  # type: ignore[name-defined]
    required = {
        "ingestion_status",
        "source_system_code",
        "source_record_reference",
        "source_version",
        "source_snapshot_id",
        "ingestion_attempt_id",
        "payload_hash",
        "ingested_at",
    }
    missing = sorted(required.difference(dataframe.columns))
    if missing:
        raise RuntimeError(
            "Bronze table %s is missing required columns: %s"
            % (table_name, ", ".join(missing))
        )
    dataframe = dataframe.where(F.col("ingestion_status") == F.lit("accepted"))
    if config.source_snapshot_id:
        dataframe = dataframe.where(
            F.col("source_snapshot_id") == F.lit(config.source_snapshot_id)
        )
    if config.ingestion_attempt_id:
        dataframe = dataframe.where(
            F.col("ingestion_attempt_id") == F.lit(config.ingestion_attempt_id)
        )
    return dataframe


def column_or_null(
    dataframe: DataFrame,
    candidates: Sequence[str],
    data_type: str,
    default=None,
):
    for candidate in candidates:
        if candidate in dataframe.columns:
            return F.col(candidate).cast(data_type)
    return F.lit(default).cast(data_type)


def stable_id(*columns):
    return F.xxhash64(
        *[F.coalesce(F.col(c).cast("string"), F.lit("")) for c in columns]
    )


def first_column(dataframe: DataFrame, candidates: Sequence[str]) -> Optional[str]:
    return next((candidate for candidate in candidates if candidate in dataframe.columns), None)


def normalize_timestamp(dataframe: DataFrame, candidates: Sequence[str]):
    for candidate in candidates:
        if candidate in dataframe.columns:
            return F.to_utc_timestamp(F.to_timestamp(F.col(candidate)), "UTC")
    return F.lit(None).cast("timestamp")


def current_version(
    dataframe: DataFrame,
    business_keys: Sequence[str],
) -> DataFrame:
    if not business_keys:
        raise ValueError("At least one Silver business key is required")
    ordering = [
        F.coalesce(F.col("source_version").cast("long"), F.lit(0)).desc(),
        F.col("source_event_timestamp").desc_nulls_last(),
        F.col("ingested_at").desc_nulls_last(),
        F.col("payload_hash").desc(),
    ]
    window = Window.partitionBy(*business_keys).orderBy(*ordering)
    return (
        dataframe.withColumn("_silver_rank", F.row_number().over(window))
        .withColumn("is_current", F.col("_silver_rank") == 1)
        .drop("_silver_rank")
    )


def add_lineage(
    dataframe: DataFrame,
    transformation_run_id: str,
    quality_status: str = "valid",
    quality_reason=None,
) -> DataFrame:
    payload_column = (
        F.col("payload_hash")
        if "payload_hash" in dataframe.columns
        else F.col("bronze_payload_hash")
    )
    effective_from = (
        F.coalesce(F.col("source_event_timestamp"), F.col("ingested_at"))
        if "source_event_timestamp" in dataframe.columns
        else F.current_timestamp()
    )
    return (
        dataframe.withColumn(
            "bronze_payload_hash",
            payload_column.cast("string"),
        )
        .withColumn("transformation_run_id", F.lit(transformation_run_id))
        .withColumn("transformed_at", F.current_timestamp())
        .withColumn("silver_record_version", F.lit(1).cast("long"))
        .withColumn("effective_from", effective_from)
        .withColumn("effective_to", F.lit(None).cast("timestamp"))
        .withColumn("quality_status", F.lit(quality_status))
        .withColumn("quality_reason", F.lit(quality_reason).cast("string"))
    )


def add_analytical_lineage(
    dataframe: DataFrame,
    transformation_run_id: str,
    quality_status: str = "valid",
    quality_reason=None,
    evidence_status: str = "source_derived",
    confidence=None,
) -> DataFrame:
    result = add_lineage(
        dataframe,
        transformation_run_id,
        quality_status,
        quality_reason,
    )
    return (
        result.withColumn("evidence_status", F.lit(evidence_status))
        .withColumn("confidence", F.lit(confidence).cast("double"))
        .withColumn("unresolved_reason", F.lit(None).cast("string"))
        .withColumn("calculation_run_id", F.lit(transformation_run_id))
    )


def validate_required(
    dataframe: DataFrame,
    required_columns: Sequence[str],
    reason: str,
) -> DataFrame:
    invalid = None
    for column in required_columns:
        condition = F.col(column).isNull()
        invalid = condition if invalid is None else invalid | condition
    return dataframe.withColumn(
        "_quality_reason",
        F.when(invalid, F.lit(reason)).otherwise(F.lit(None).cast("string")),
    )


def merge_current(
    dataframe: DataFrame,
    target_table: str,
    business_keys: Sequence[str],
    partition_columns: Sequence[str] = (),
) -> Dict[str, int]:
    if dataframe.rdd.isEmpty():
        return {"input_count": 0, "current_count": 0, "duplicate_count": 0}
    current = dataframe.where(F.col("is_current") == F.lit(True))
    input_count = dataframe.count()
    current_count = current.count()
    duplicate_count = input_count - current_count
    for column in partition_columns:
        if column not in current.columns:
            current = current.withColumn(column, F.lit(None).cast("string"))
    if not _exists(target_table):
        current.write.format("delta").mode("overwrite").partitionBy(
            *partition_columns
        ).saveAsTable(target_table)
    else:
        target = DeltaTable.forName(spark, target_table)  # type: ignore[name-defined]
        condition = " AND ".join(
            "target.`%s` <=> source.`%s`" % (key, key)
            for key in business_keys
        )
        (
            target.alias("target")
            .merge(current.alias("source"), condition)
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )
    return {
        "input_count": input_count,
        "current_count": current_count,
        "duplicate_count": duplicate_count,
    }


def publish_metrics(task_name: str, metrics: Dict[str, int]) -> None:
    LOGGER.info("Silver task=%s metrics=%s", task_name, metrics)
    try:
        for key, value in metrics.items():
            dbutils.jobs.taskValues.set(  # type: ignore[name-defined]
                key="%s_%s" % (task_name, key),
                value=str(int(value)),
            )
    except NameError:
        raise RuntimeError("Silver metrics require a Databricks job runtime")


def ensure_quality_table(config) -> None:
    table_name = "%s._quality_record" % config.silver_database
    if _exists(table_name):
        return
    schema = T.StructType(
        [
            T.StructField("quality_record_id", T.StringType(), False),
            T.StructField("table_name", T.StringType(), False),
            T.StructField("rule_code", T.StringType(), False),
            T.StructField("severity", T.StringType(), False),
            T.StructField("quality_status", T.StringType(), False),
            T.StructField("quality_reason", T.StringType(), False),
            T.StructField("source_snapshot_id", T.StringType(), True),
            T.StructField("ingestion_attempt_id", T.StringType(), True),
            T.StructField("transformation_run_id", T.StringType(), False),
            T.StructField("detected_at", T.TimestampType(), False),
        ]
    )
    spark.createDataFrame([], schema).write.format("delta").mode("overwrite").saveAsTable(
        table_name
    )
