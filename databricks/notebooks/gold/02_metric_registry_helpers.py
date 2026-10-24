# Databricks notebook source
"""Metric registry helpers for versioned Gold calculations."""

from pyspark.sql import functions as F
from delta.tables import DeltaTable


def ensure_metric_definition_table(config):
    table_name = config.gold_table("quality", "metric_definition")
    if spark.catalog.tableExists(table_name):  # type: ignore[name-defined]
        return
    schema = (
        "metric_code string, metric_version string, metric_name string, "
        "formula string, denominator_policy string, minimum_sample_size int, "
        "owner string, active_flag boolean, created_at timestamp"
    )
    spark.createDataFrame([], schema).write.format("delta").mode("overwrite").saveAsTable(
        table_name
    )


def register_metric(config, metric_code: str, metric_name: str, formula: str, denominator_policy: str):
    ensure_metric_definition_table(config)
    row = spark.createDataFrame(  # type: ignore[name-defined]
        [(metric_code, config.metric_version, metric_name, formula, denominator_policy,
          config.minimum_sample_size, "offball-data-platform", True)],
        "metric_code string, metric_version string, metric_name string, formula string, "
        "denominator_policy string, minimum_sample_size int, owner string, active_flag boolean",
    ).withColumn("created_at", F.current_timestamp())
    table_name = config.gold_table("quality", "metric_definition")
    target = DeltaTable.forName(spark, table_name)  # type: ignore[name-defined]
    (
        target.alias("target")
        .merge(
            row.alias("source"),
            "target.metric_code = source.metric_code AND "
            "target.metric_version = source.metric_version",
        )
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
