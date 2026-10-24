# Databricks notebook source
# MAGIC %run ./00_silver_runtime_config
# MAGIC %run ./01_silver_helpers
# MAGIC %run ./02_quality_helpers
# MAGIC %run ./04_temporal_helpers

from pyspark.sql import functions as F


def main():
    config = SILVER_CONFIG
    ensure_operational_outputs(config)
    source = spark.table(config.silver_table("event", "fixture"))  # type: ignore[name-defined]
    periods = source.select(
        stable_id("source_system_code", "fixture_id").alias("match_period_id"),
        "fixture_id",
        F.lit("match").alias("period_type"),
        F.lit(1).cast("int").alias("period_number"),
        F.col("actual_start_timestamp").alias("start_timestamp"),
        F.col("actual_end_timestamp").alias("end_timestamp"),
        "source_system_code", "source_snapshot_id", "ingestion_attempt_id",
        "source_record_reference", "source_version", "bronze_payload_hash",
    )
    periods = validate_interval(
        periods, "start_timestamp", "end_timestamp", "match period timestamps are invalid"
    )
    periods = validate_required(
        periods, ("fixture_id", "start_timestamp"), "match period identity or start is missing"
    )
    invalid = periods.where(F.col("_quality_reason").isNotNull())
    valid = periods.where(F.col("_quality_reason").isNull()).drop("_quality_reason")
    invalid = add_analytical_lineage(invalid, config.transformation_run_id, "quarantined")
    write_quality_records(
        invalid,
        config,
        "silver.analytics.match_period",
        "MATCH_PERIOD_REQUIRED",
        "high",
    )
    valid = add_analytical_lineage(valid, config.transformation_run_id, confidence=1.0)
    metrics = merge_current(valid, config.silver_table("analytics", "match_period"), ("match_period_id",))
    metrics["quarantined_count"] = invalid.count()
    publish_metrics("build_match_period", metrics)
    return metrics


if __name__ == "__main__":
    main()
