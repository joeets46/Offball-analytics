# Databricks notebook source
# MAGIC %run ./00_silver_runtime_config
# MAGIC %run ./01_silver_helpers
# MAGIC %run ./02_quality_helpers

from pyspark.sql import functions as F


def main():
    config = SILVER_CONFIG
    ensure_quality_table(config)
    source = source_rows(config, "athlete_profile_raw")
    projected = (
        source.select(
            column_or_null(source, ("athlete_profile_id", "athlete_id", "provider_athlete_id"), "long").alias("athlete_profile_id"),
            column_or_null(source, ("preferred_name", "display_name", "name"), "string").alias("preferred_name"),
            column_or_null(source, ("legal_name",), "string").alias("legal_name"),
            column_or_null(source, ("date_of_birth", "birth_date"), "date").alias("date_of_birth"),
            column_or_null(source, ("nationality_code", "nationality"), "string").alias("nationality_code"),
            column_or_null(source, ("career_status", "status"), "string").alias("career_status"),
            "source_system_code", "source_record_reference", "source_version",
            "source_snapshot_id", "ingestion_attempt_id", "payload_hash",
            normalize_timestamp(source, ("updated_timestamp", "source_event_timestamp")).alias("source_event_timestamp"),
            "ingested_at",
        )
    )
    projected = validate_required(
        projected,
        ("athlete_profile_id", "preferred_name", "source_system_code", "source_record_reference"),
        "athlete identity or preferred name is missing",
    )
    invalid = projected.where(F.col("_quality_reason").isNotNull())
    valid = projected.where(F.col("_quality_reason").isNull()).drop("_quality_reason")
    invalid = add_lineage(invalid, config.transformation_run_id, "quarantined")
    write_quality_records(
        invalid,
        config,
        "silver.athlete.athlete_profile",
        "ATHLETE_PROFILE_REQUIRED",
        "high",
    )
    valid = add_lineage(valid, config.transformation_run_id)
    valid = current_version(valid, ("source_system_code", "source_record_reference"))
    metrics = merge_current(
        valid,
        config.silver_table("athlete", "athlete_profile"),
        ("source_system_code", "source_record_reference"),
    )
    metrics["quarantined_count"] = invalid.count()
    publish_metrics("conform_athlete_profile", metrics)
    return metrics


if __name__ == "__main__":
    main()
