# Databricks notebook source
# MAGIC %run ./00_silver_runtime_config
# MAGIC %run ./01_silver_helpers
# MAGIC %run ./02_quality_helpers

from pyspark.sql import functions as F


def main():
    config = SILVER_CONFIG
    ensure_operational_outputs(config)
    phases = spark.table(config.silver_table("analytics", "phase_interval")).where("is_current = true")  # type: ignore[name-defined]
    participants = spark.table(config.silver_table("event", "participant")).where("is_current = true")  # type: ignore[name-defined]
    opportunities = phases.join(participants, "fixture_id", "inner").select(
        stable_id("phase_interval_id", "participant_id").alias("opportunity_id"),
        "fixture_id", "participant_id", "phase_interval_id",
        F.lit("participant_phase").alias("opportunity_type"),
        F.lit(True).alias("eligible_flag"),
        F.lit(True).alias("observed_flag"),
        "start_timestamp", "end_timestamp",
        F.lit("source_derived").alias("evidence_status"),
        "source_system_code", "source_record_reference", "source_version",
        "source_snapshot_id", "ingestion_attempt_id", "bronze_payload_hash",
    )
    opportunities = validate_required(
        opportunities,
        ("fixture_id", "participant_id", "start_timestamp"),
        "opportunity reference is incomplete",
    )
    invalid = opportunities.where(F.col("_quality_reason").isNotNull())
    valid = opportunities.where(F.col("_quality_reason").isNull()).drop("_quality_reason")
    invalid = add_analytical_lineage(invalid, config.transformation_run_id, "quarantined")
    write_quality_records(invalid, config, "silver.analytics.opportunity", "OPPORTUNITY_REQUIRED", "high")
    valid = add_analytical_lineage(valid, config.transformation_run_id, confidence=0.5)
    metrics = merge_current(valid, config.silver_table("analytics", "opportunity"), ("opportunity_id",))
    metrics["quarantined_count"] = invalid.count()
    publish_metrics("build_opportunity", metrics)
    return metrics


if __name__ == "__main__":
    main()
