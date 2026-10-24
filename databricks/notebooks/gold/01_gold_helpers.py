# Databricks notebook source
"""Shared Gold metric, aggregation, lineage, and Delta MERGE helpers."""

from typing import Dict, Sequence
import logging

from delta.tables import DeltaTable
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


LOGGER = logging.getLogger("offball.sprint3.gold")
if not LOGGER.handlers:
    LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.INFO)


COMMON_GOLD_COLUMNS = (
    "metric_code",
    "metric_version",
    "evaluation_window_type",
    "numerator",
    "denominator",
    "metric_value",
    "sample_size",
    "coverage_ratio",
    "confidence",
    "quality_status",
    "quality_reason",
    "calculation_run_id",
    "publication_status",
    "refreshed_at",
)


def safe_ratio(numerator, denominator, minimum_sample_size: int):
    return F.when(
        denominator >= F.lit(minimum_sample_size),
        numerator.cast("double") / F.nullif(denominator.cast("double"), F.lit(0)),
    ).otherwise(F.lit(None).cast("double"))


def metric_status(denominator, minimum_sample_size: int):
    return F.when(
        denominator < F.lit(minimum_sample_size),
        F.lit("insufficient_sample"),
    ).otherwise(F.lit("published"))


def silver_current(config, domain: str, table: str) -> DataFrame:
    name = config.silver_table(domain, table)
    if not spark.catalog.tableExists(name):  # type: ignore[name-defined]
        raise RuntimeError("Required Silver table does not exist: %s" % name)
    dataframe = spark.table(name)  # type: ignore[name-defined]
    if "quality_status" in dataframe.columns:
        dataframe = dataframe.where(
            F.col("quality_status").isin(
                "valid", "valid_with_warning", "conflict_selected"
            )
        )
    if "is_current" in dataframe.columns:
        dataframe = dataframe.where(F.col("is_current") == F.lit(True))
    return dataframe


def add_gold_contract(
    dataframe: DataFrame,
    config,
    metric_code: str,
    numerator,
    denominator,
    coverage=None,
    confidence=None,
) -> DataFrame:
    coverage_expression = (
        coverage
        if coverage is not None
        else safe_ratio(numerator, denominator, 1)
    )
    return (
        dataframe.withColumn("metric_code", F.lit(metric_code))
        .withColumn("metric_version", F.lit(config.metric_version))
        .withColumn("evaluation_window_type", F.lit(config.evaluation_window_type))
        .withColumn("evaluation_window_start", F.to_date(F.lit(config.evaluation_window_start)))
        .withColumn("evaluation_window_end", F.to_date(F.lit(config.evaluation_window_end)))
        .withColumn("numerator", numerator.cast("double"))
        .withColumn("denominator", denominator.cast("double"))
        .withColumn(
            "metric_value",
            safe_ratio(numerator, denominator, config.minimum_sample_size),
        )
        .withColumn("sample_size", denominator.cast("long"))
        .withColumn("coverage_ratio", coverage_expression.cast("double"))
        .withColumn("confidence", confidence.cast("double") if confidence is not None else F.lit(None).cast("double"))
        .withColumn(
            "quality_status",
            metric_status(denominator, config.minimum_sample_size),
        )
        .withColumn(
            "quality_reason",
            F.when(
                denominator < F.lit(config.minimum_sample_size),
                F.lit("denominator below metric threshold"),
            ).otherwise(F.lit(None).cast("string")),
        )
        .withColumn("calculation_run_id", F.lit(config.calculation_run_id))
        .withColumn("publication_status", F.lit("published"))
        .withColumn("published_at", F.current_timestamp())
        .withColumn("refreshed_at", F.current_timestamp())
    )


def merge_gold(dataframe: DataFrame, target_table: str, merge_keys: Sequence[str]) -> Dict[str, int]:
    if dataframe.rdd.isEmpty():
        return {"input_count": 0, "output_count": 0}
    input_count = dataframe.count()
    if not spark.catalog.tableExists(target_table):  # type: ignore[name-defined]
        dataframe.write.format("delta").mode("overwrite").saveAsTable(target_table)
    else:
        target = DeltaTable.forName(spark, target_table)  # type: ignore[name-defined]
        condition = " AND ".join(
            "target.`%s` <=> source.`%s`" % (key, key) for key in merge_keys
        )
        (
            target.alias("target")
            .merge(dataframe.alias("source"), condition)
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )
    return {"input_count": input_count, "output_count": input_count}


def publish_metrics(task_name: str, metrics: Dict[str, int]) -> None:
    LOGGER.info("Gold task=%s metrics=%s", task_name, metrics)
    try:
        for key, value in metrics.items():
            dbutils.jobs.taskValues.set(  # type: ignore[name-defined]
                key="%s_%s" % (task_name, key),
                value=str(int(value)),
            )
    except NameError as exc:
        raise RuntimeError("Gold metrics require a Databricks job runtime") from exc


def publish_lineage_columns(dataframe: DataFrame) -> DataFrame:
    columns = set(dataframe.columns)
    return (
        dataframe.withColumn(
            "source_snapshot_id",
            F.col("source_snapshot_id") if "source_snapshot_id" in columns else F.lit(None).cast("string"),
        )
        .withColumn(
            "ingestion_attempt_id",
            F.col("ingestion_attempt_id") if "ingestion_attempt_id" in columns else F.lit(None).cast("string"),
        )
        .withColumn(
            "transformation_run_id",
            F.col("transformation_run_id") if "transformation_run_id" in columns else F.lit(None).cast("string"),
        )
    )
