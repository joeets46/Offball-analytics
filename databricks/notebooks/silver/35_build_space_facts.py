# Databricks notebook source
# MAGIC %run ./00_silver_runtime_config
# MAGIC %run ./01_silver_helpers
# MAGIC %run ./02_quality_helpers

from pyspark.sql import functions as F


def _write(config, dataframe, domain_table, keys, task_name):
    dataframe = add_analytical_lineage(dataframe, config.transformation_run_id, confidence=0.5)
    metrics = merge_current(dataframe, config.silver_table("analytics", domain_table), keys)
    publish_metrics(task_name, metrics)
    return metrics


def main():
    config = SILVER_CONFIG
    ensure_operational_outputs(config)
    opportunities = spark.table(config.silver_table("analytics", "opportunity")).where("is_current = true")  # type: ignore[name-defined]
    space = opportunities.select(
        stable_id("opportunity_id", "participant_id").alias("space_opportunity_id"),
        "opportunity_id", "participant_id",
        F.lit("movement").alias("space_type"),
        F.lit(None).cast("string").alias("target_zone"),
        F.lit(None).cast("double").alias("expected_value_delta"),
        F.lit("unresolved").alias("outcome_status"),
        "source_system_code", "source_record_reference", "source_version",
        "source_snapshot_id", "ingestion_attempt_id", "bronze_payload_hash",
    )
    baseline = space.select(
        stable_id("space_opportunity_id", "space_type").alias("space_baseline_id"),
        "space_opportunity_id", F.lit("tracking_unavailable").alias("baseline_method"),
        F.to_json(F.struct(F.lit(None).cast("double").alias("coverage"))).alias("baseline_value"),
        F.lit(None).cast("string").alias("counterfactual_reference"),
        "source_system_code", "source_record_reference", "source_version",
        "source_snapshot_id", "ingestion_attempt_id", "bronze_payload_hash",
    )
    counterfactual = space.select(
        stable_id("space_opportunity_id", "outcome_status").alias("space_counterfactual_id"),
        "space_opportunity_id", F.lit("tracking_unavailable").alias("counterfactual_type"),
        F.lit(None).cast("double").alias("expected_value_delta"),
        "source_system_code", "source_record_reference", "source_version",
        "source_snapshot_id", "ingestion_attempt_id", "bronze_payload_hash",
    )
    outcome = space.select(
        stable_id("space_opportunity_id", "outcome_status").alias("space_outcome_id"),
        "space_opportunity_id", "outcome_status",
        "source_system_code", "source_record_reference", "source_version",
        "source_snapshot_id", "ingestion_attempt_id", "bronze_payload_hash",
    )
    return {
        "space_opportunity": _write(config, space, "space_opportunity", ("space_opportunity_id",), "build_space_opportunity"),
        "space_baseline": _write(config, baseline, "space_baseline", ("space_baseline_id",), "build_space_baseline"),
        "space_counterfactual": _write(config, counterfactual, "space_counterfactual", ("space_counterfactual_id",), "build_space_counterfactual"),
        "space_outcome": _write(config, outcome, "space_outcome", ("space_outcome_id",), "build_space_outcome"),
    }


if __name__ == "__main__":
    main()
