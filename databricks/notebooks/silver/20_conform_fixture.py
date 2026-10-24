# Databricks notebook source
# MAGIC %run ./00_silver_runtime_config
# MAGIC %run ./01_silver_helpers
# MAGIC %run ./02_quality_helpers
# MAGIC %run ./04_temporal_helpers

from pyspark.sql import functions as F


def main():
    config = SILVER_CONFIG
    ensure_quality_table(config)
    source = source_rows(config, "fixture_raw")
    projected = source.select(
        column_or_null(source, ("fixture_id", "provider_fixture_id"), "long").alias("fixture_id"),
        column_or_null(source, ("calendar_id",), "long").alias("calendar_id"),
        column_or_null(source, ("tournament_id", "competition_id"), "long").alias("tournament_id"),
        column_or_null(source, ("competition_round_id", "round_id"), "long").alias("competition_round_id"),
        column_or_null(source, ("type_id", "fixture_type_id"), "long").alias("type_id"),
        column_or_null(source, ("season_id",), "long").alias("season_id"),
        column_or_null(source, ("fixture_code", "fixture_reference"), "string").alias("fixture_code"),
        column_or_null(source, ("event_date", "fixture_date"), "date").alias("event_date"),
        normalize_timestamp(source, ("actual_start_timestamp", "start_timestamp", "event_timestamp")).alias("actual_start_timestamp"),
        normalize_timestamp(source, ("actual_end_timestamp", "end_timestamp")).alias("actual_end_timestamp"),
        column_or_null(source, ("lifecycle_status", "status"), "string").alias("lifecycle_status"),
        "source_system_code", "source_record_reference", "source_version",
        "source_snapshot_id", "ingestion_attempt_id", "payload_hash", "ingested_at",
    )
    projected = validate_interval(
        projected,
        "actual_start_timestamp",
        "actual_end_timestamp",
        "fixture timestamps are invalid",
    )
    projected = validate_required(
        projected,
        ("fixture_id", "source_system_code", "source_record_reference"),
        "fixture identity is missing",
    )
    invalid = projected.where(F.col("_quality_reason").isNotNull())
    valid = projected.where(F.col("_quality_reason").isNull()).drop("_quality_reason")
    invalid = add_lineage(invalid, config.transformation_run_id, "quarantined")
    write_quality_records(
        invalid,
        config,
        "silver.event.fixture",
        "FIXTURE_REQUIRED",
        "high",
    )
    valid = add_lineage(valid, config.transformation_run_id)
    valid = current_version(valid, ("source_system_code", "source_record_reference"))
    metrics = merge_current(
        valid,
        config.silver_table("event", "fixture"),
        ("source_system_code", "source_record_reference"),
    )
    metrics["quarantined_count"] = invalid.count()
    publish_metrics("conform_fixture", metrics)
    return metrics


if __name__ == "__main__":
    main()
