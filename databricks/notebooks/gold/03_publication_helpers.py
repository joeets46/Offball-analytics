# Databricks notebook source
"""Gold calculation-run and publication lifecycle helpers."""

from pyspark.sql import functions as F
from delta.tables import DeltaTable


def ensure_publication_tables(config):
    definitions = {
        "calculation_run": "calculation_run_id string, metric_version string, status string, started_at timestamp, completed_at timestamp",
        "metric_publication": "calculation_run_id string, publication_status string, published_at timestamp, refreshed_at timestamp",
        "data_freshness": "product_name string, calculation_run_id string, refreshed_at timestamp, freshness_status string",
        "metric_exception": "exception_id string, metric_code string, reason string, calculation_run_id string, created_at timestamp",
    }
    for table, schema in definitions.items():
        name = config.gold_table("quality", table)
        if not spark.catalog.tableExists(name):  # type: ignore[name-defined]
            spark.createDataFrame([], schema).write.format("delta").mode("overwrite").saveAsTable(name)


def register_calculation_run(config):
    ensure_publication_tables(config)
    row = spark.createDataFrame(  # type: ignore[name-defined]
        [(config.calculation_run_id, config.metric_version, "running")],
        "calculation_run_id string, metric_version string, status string",
    ).withColumn("started_at", F.current_timestamp()).withColumn(
        "completed_at", F.lit(None).cast("timestamp")
    )
    table_name = config.gold_table("quality", "calculation_run")
    target = DeltaTable.forName(spark, table_name)  # type: ignore[name-defined]
    (
        target.alias("target")
        .merge(row.alias("source"), "target.calculation_run_id = source.calculation_run_id")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )


def finalize_publication(config, status: str = "published"):
    ensure_publication_tables(config)
    row = spark.createDataFrame(  # type: ignore[name-defined]
        [(config.calculation_run_id, status)],
        "calculation_run_id string, publication_status string",
    ).withColumn("published_at", F.current_timestamp()).withColumn(
        "refreshed_at", F.current_timestamp()
    )
    table_name = config.gold_table("quality", "metric_publication")
    target = DeltaTable.forName(spark, table_name)  # type: ignore[name-defined]
    (
        target.alias("target")
        .merge(row.alias("source"), "target.calculation_run_id = source.calculation_run_id")
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
