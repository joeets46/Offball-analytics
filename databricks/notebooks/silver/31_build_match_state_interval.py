# Databricks notebook source
# MAGIC %run ./00_silver_runtime_config
# MAGIC %run ./01_silver_helpers
# MAGIC %run ./02_quality_helpers

from pyspark.sql import functions as F


def main():
    config = SILVER_CONFIG
    ensure_operational_outputs(config)
    periods = spark.table(config.silver_table("analytics", "match_period")).where("is_current = true")  # type: ignore[name-defined]
    results = spark.table(config.silver_table("event", "match_result")).where("is_current = true")  # type: ignore[name-defined]
    states = periods.alias("period").join(
        results.alias("result"), "fixture_id", "left"
    ).select(
        stable_id("match_period_id", "home_score", "away_score").alias("match_state_interval_id"),
        F.col("period.match_period_id").alias("match_period_id"),
        F.col("period.fixture_id").alias("fixture_id"),
        F.coalesce(F.col("result.home_score"), F.lit(0)).cast("int").alias("home_score"),
        F.coalesce(F.col("result.away_score"), F.lit(0)).cast("int").alias("away_score"),
        F.when(F.col("result.home_score") == F.col("result.away_score"), "draw")
        .when(F.col("result.home_score") > F.col("result.away_score"), "home_leading")
        .otherwise("away_leading").alias("numerical_state"),
        F.col("period.start_timestamp").alias("start_timestamp"),
        F.col("period.end_timestamp").alias("end_timestamp"),
        F.lit("source_derived").alias("evidence_status"),
        F.col("period.source_snapshot_id").alias("source_snapshot_id"),
        F.col("period.ingestion_attempt_id").alias("ingestion_attempt_id"),
        F.col("period.source_system_code").alias("source_system_code"),
        F.col("period.source_record_reference").alias("source_record_reference"),
        F.col("period.source_version").alias("source_version"),
        F.col("period.bronze_payload_hash").alias("bronze_payload_hash"),
    )
    states = validate_required(states, ("match_period_id", "start_timestamp"), "match state interval is incomplete")
    invalid = states.where(F.col("_quality_reason").isNotNull())
    valid = states.where(F.col("_quality_reason").isNull()).drop("_quality_reason")
    invalid = add_analytical_lineage(invalid, config.transformation_run_id, "quarantined")
    write_quality_records(
        invalid,
        config,
        "silver.analytics.match_state_interval",
        "MATCH_STATE_REQUIRED",
        "high",
    )
    valid = add_analytical_lineage(valid, config.transformation_run_id, confidence=0.95)
    metrics = merge_current(valid, config.silver_table("analytics", "match_state_interval"), ("match_state_interval_id",))
    metrics["quarantined_count"] = invalid.count()
    publish_metrics("build_match_state_interval", metrics)
    return metrics


if __name__ == "__main__":
    main()
