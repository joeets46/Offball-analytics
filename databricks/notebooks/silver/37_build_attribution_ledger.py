# Databricks notebook source
# MAGIC %run ./00_silver_runtime_config
# MAGIC %run ./01_silver_helpers
# MAGIC %run ./02_quality_helpers

from pyspark.sql import functions as F


def main():
    config = SILVER_CONFIG
    ensure_operational_outputs(config)
    space = spark.table(config.silver_table("analytics", "space_opportunity")).where("is_current = true")  # type: ignore[name-defined]
    pressing = spark.table(config.silver_table("analytics", "pressing_opportunity")).where("is_current = true")  # type: ignore[name-defined]
    space_rows = space.select(
        stable_id("space_opportunity_id", "participant_id").alias("attribution_id"),
        "space_opportunity_id",
        F.lit(None).cast("long").alias("pressing_opportunity_id"),
        "participant_id",
        F.lit("space_creation").alias("attribution_type"),
        F.lit(1.0).cast("double").alias("attribution_share"),
        F.lit(None).cast("long").alias("evidence_link_id"),
        "source_system_code", "source_record_reference", "source_version",
        "source_snapshot_id", "ingestion_attempt_id", "bronze_payload_hash",
    )
    press_rows = pressing.select(
        stable_id("pressing_opportunity_id", "participant_id").alias("attribution_id"),
        F.lit(None).cast("long").alias("space_opportunity_id"),
        "pressing_opportunity_id", "participant_id",
        F.lit("pressing").alias("attribution_type"),
        F.lit(1.0).cast("double").alias("attribution_share"),
        F.lit(None).cast("long").alias("evidence_link_id"),
        "source_system_code", "source_record_reference", "source_version",
        "source_snapshot_id", "ingestion_attempt_id", "bronze_payload_hash",
    )
    rows = space_rows.unionByName(press_rows)
    rows = rows.withColumn(
        "_quality_reason",
        F.when(
            (F.col("participant_id").isNull())
            | (F.col("attribution_share") < 0)
            | (F.col("attribution_share") > 1),
            F.lit("attribution participant or share is invalid"),
        ),
    )
    invalid = rows.where(F.col("_quality_reason").isNotNull())
    valid = rows.where(F.col("_quality_reason").isNull()).drop("_quality_reason")
    invalid = add_analytical_lineage(invalid, config.transformation_run_id, "quarantined")
    write_quality_records(invalid, config, "silver.analytics.attribution_ledger", "ATTRIBUTION_INVALID", "high")
    valid = add_analytical_lineage(valid, config.transformation_run_id, confidence=0.5)
    metrics = merge_current(valid, config.silver_table("analytics", "attribution_ledger"), ("attribution_id",))
    metrics["quarantined_count"] = invalid.count()
    publish_metrics("build_attribution_ledger", metrics)
    return metrics


if __name__ == "__main__":
    main()
