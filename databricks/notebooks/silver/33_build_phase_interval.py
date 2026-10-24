# Databricks notebook source
# MAGIC %run ./00_silver_runtime_config
# MAGIC %run ./01_silver_helpers
# MAGIC %run ./02_quality_helpers

from pyspark.sql import functions as F


def main():
    config = SILVER_CONFIG
    ensure_operational_outputs(config)
    possessions = spark.table(config.silver_table("analytics", "possession_sequence")).where("is_current = true")  # type: ignore[name-defined]
    phases = possessions.select(
        stable_id("possession_sequence_id", "phase_version").alias("phase_interval_id"),
        "possession_sequence_id", "fixture_id",
        F.lit("possession").alias("phase_type"),
        "start_timestamp", "end_timestamp",
        "source_system_code", "source_record_reference", "source_version",
        "source_snapshot_id", "ingestion_attempt_id", "bronze_payload_hash",
    )
    phases = validate_required(phases, ("possession_sequence_id", "fixture_id", "start_timestamp"), "phase interval is incomplete")
    invalid = phases.where(F.col("_quality_reason").isNotNull())
    valid = phases.where(F.col("_quality_reason").isNull()).drop("_quality_reason")
    invalid = add_analytical_lineage(invalid, config.transformation_run_id, "quarantined")
    write_quality_records(
        invalid,
        config,
        "silver.analytics.phase_interval",
        "PHASE_REQUIRED",
        "high",
    )
    valid = add_analytical_lineage(valid, config.transformation_run_id, confidence=0.5, evidence_status="inferred")
    metrics = merge_current(valid, config.silver_table("analytics", "phase_interval"), ("phase_interval_id",))
    metrics["quarantined_count"] = invalid.count()
    publish_metrics("build_phase_interval", metrics)
    return metrics


if __name__ == "__main__":
    main()
