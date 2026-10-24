# Databricks notebook source
# MAGIC %run ./00_silver_runtime_config
# MAGIC %run ./01_silver_helpers
# MAGIC %run ./02_quality_helpers

from pyspark.sql import functions as F


def main():
    config = SILVER_CONFIG
    ensure_operational_outputs(config)
    opportunities = spark.table(config.silver_table("analytics", "opportunity")).where("is_current = true")  # type: ignore[name-defined]
    pressing = opportunities.select(
        stable_id("opportunity_id", "participant_id").alias("pressing_opportunity_id"),
        "opportunity_id", "participant_id",
        F.lit("pressure").alias("press_type"),
        F.lit(None).cast("long").alias("target_participant_id"),
        F.lit("event_derived").alias("trigger_type"),
        F.lit("unresolved").alias("outcome_status"),
        "source_system_code", "source_record_reference", "source_version",
        "source_snapshot_id", "ingestion_attempt_id", "bronze_payload_hash",
    )

    def derived(name, columns):
        return pressing.select(
            stable_id("pressing_opportunity_id", "participant_id").alias(name),
            *columns,
            "source_system_code", "source_record_reference", "source_version",
            "source_snapshot_id", "ingestion_attempt_id", "bronze_payload_hash",
        )

    trigger = derived("press_trigger_id", ["pressing_opportunity_id", "trigger_type", F.lit(None).cast("timestamp").alias("trigger_timestamp")])
    action = derived("press_action_id", ["pressing_opportunity_id", "participant_id", F.lit("unresolved").alias("action_type"), F.lit(None).cast("timestamp").alias("action_timestamp"), F.lit(None).cast("double").alias("intensity")])
    support = derived("press_support_id", ["pressing_opportunity_id", "participant_id", F.lit("unresolved").alias("support_type")])
    bypass = derived("press_bypass_id", ["pressing_opportunity_id", F.lit("unresolved").alias("bypass_type"), F.lit(None).cast("timestamp").alias("bypass_timestamp")])
    outcome = derived("press_outcome_id", ["pressing_opportunity_id", F.col("outcome_status").alias("outcome_type"), F.lit(None).cast("double").alias("outcome_value")])
    recovery = derived("recovery_action_id", ["pressing_opportunity_id", "participant_id", F.lit("unresolved").alias("action_type"), F.lit(None).cast("timestamp").alias("action_timestamp")])
    results = {"pressing_opportunity": _merge(config, pressing, "pressing_opportunity", ("pressing_opportunity_id",), "build_pressing_opportunity")}
    for data, table, key, task in (
        (trigger, "press_trigger", "press_trigger_id", "build_press_trigger"),
        (action, "press_action", "press_action_id", "build_press_action"),
        (support, "press_support", "press_support_id", "build_press_support"),
        (bypass, "press_bypass", "press_bypass_id", "build_press_bypass"),
        (outcome, "press_outcome", "press_outcome_id", "build_press_outcome"),
        (recovery, "recovery_action", "recovery_action_id", "build_recovery_action"),
    ):
        results[table] = _merge(config, data, table, (key,), task)
    return results


def _merge(config, dataframe, table, keys, task):
    dataframe = add_analytical_lineage(dataframe, config.transformation_run_id, confidence=0.5, evidence_status="inferred")
    metrics = merge_current(dataframe, config.silver_table("analytics", table), keys)
    publish_metrics(task, metrics)
    return metrics


if __name__ == "__main__":
    main()
