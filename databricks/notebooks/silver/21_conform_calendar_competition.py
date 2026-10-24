# Databricks notebook source
# MAGIC %run ./00_silver_runtime_config
# MAGIC %run ./01_silver_helpers
# MAGIC %run ./02_quality_helpers

from pyspark.sql import functions as F


def _conform(config, source_name, domain, target_name, id_candidates, name_candidates):
    source = source_rows(config, "competition_raw")
    projected = source.select(
        column_or_null(source, id_candidates, "long").alias(target_name + "_id"),
        column_or_null(source, name_candidates, "string").alias(target_name + "_name"),
        "source_system_code", "source_record_reference", "source_version",
        "source_snapshot_id", "ingestion_attempt_id", "payload_hash", "ingested_at",
        normalize_timestamp(source, ("source_event_timestamp", "updated_timestamp")).alias(
            "source_event_timestamp"
        ),
    )
    projected = validate_required(
        projected,
        (target_name + "_id",),
        "%s identity is missing" % target_name,
    )
    invalid = projected.where(F.col("_quality_reason").isNotNull())
    valid = projected.where(F.col("_quality_reason").isNull()).drop("_quality_reason")
    invalid = add_lineage(invalid, config.transformation_run_id, "quarantined")
    write_quality_records(
        invalid,
        config,
        "silver.%s.%s" % (domain, target_name),
        "COMPETITION_REFERENCE_REQUIRED",
        "medium",
    )
    valid = add_lineage(valid, config.transformation_run_id)
    valid = current_version(valid, ("source_system_code", "source_record_reference"))
    metrics = merge_current(
        valid,
        config.silver_table(domain, target_name),
        ("source_system_code", "source_record_reference"),
    )
    metrics["quarantined_count"] = invalid.count()
    publish_metrics("conform_%s" % target_name, metrics)
    return metrics


def main():
    config = SILVER_CONFIG
    ensure_quality_table(config)
    results = {}
    for target, ids, names in (
        ("calendar", ("calendar_id", "provider_calendar_id"), ("calendar_name", "name")),
        ("tournament", ("tournament_id", "competition_id"), ("tournament_name", "name")),
        ("competition_round", ("competition_round_id", "round_id"), ("round_name", "name")),
        ("type", ("type_id", "event_type_id"), ("type_name", "name")),
    ):
        results[target] = _conform(
            config,
            "competition_raw",
            "event",
            target,
            ids,
            names,
        )
    return results


if __name__ == "__main__":
    main()
