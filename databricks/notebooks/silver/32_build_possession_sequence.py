# Databricks notebook source
# MAGIC %run ./00_silver_runtime_config
# MAGIC %run ./01_silver_helpers
# MAGIC %run ./02_quality_helpers

from pyspark.sql import functions as F


def main():
    config = SILVER_CONFIG
    ensure_operational_outputs(config)
    source = source_rows(config, "event_incident_raw")
    fixture_column = first_column(source, ("fixture_id", "provider_fixture_id"))
    if not fixture_column:
        raise RuntimeError("Event incident Bronze source has no fixture reference")
    controlling = first_column(source, ("controlling_franchise_id", "team_id", "franchise_id"))
    start = first_column(source, ("possession_start_timestamp", "incident_timestamp", "source_event_timestamp"))
    end = first_column(source, ("possession_end_timestamp", "incident_end_timestamp"))
    if not start:
        raise RuntimeError("Event incident Bronze source has no possession timestamp")
    possessions = source.select(
        stable_id("source_system_code", "source_record_reference", "payload_hash").alias("possession_sequence_id"),
        F.col(fixture_column).cast("long").alias("fixture_id"),
        column_or_null(source, (controlling,) if controlling else (), "long").alias("controlling_franchise_id"),
        F.to_utc_timestamp(F.to_timestamp(F.col(start)), "UTC").alias("start_timestamp"),
        normalize_timestamp(source, (end,) if end else ()).alias("end_timestamp"),
        F.lit("inferred").alias("status"),
        F.lit("event_incident_v1").alias("phase_version"),
        F.lit("event-derived possession; tracking confirmation unavailable").alias("unresolved_reason"),
        "source_system_code", "source_record_reference", "source_version",
        "source_snapshot_id", "ingestion_attempt_id", "payload_hash",
    )
    possessions = validate_required(possessions, ("fixture_id", "start_timestamp"), "possession sequence is incomplete")
    invalid = possessions.where(F.col("_quality_reason").isNotNull())
    valid = possessions.where(F.col("_quality_reason").isNull()).drop("_quality_reason")
    invalid = add_analytical_lineage(invalid, config.transformation_run_id, "quarantined")
    write_quality_records(
        invalid,
        config,
        "silver.analytics.possession_sequence",
        "POSSESSION_REQUIRED",
        "high",
    )
    valid = add_analytical_lineage(valid, config.transformation_run_id, confidence=0.5, evidence_status="inferred")
    metrics = merge_current(valid, config.silver_table("analytics", "possession_sequence"), ("possession_sequence_id",))
    metrics["quarantined_count"] = invalid.count()
    publish_metrics("build_possession_sequence", metrics)
    return metrics


if __name__ == "__main__":
    main()
