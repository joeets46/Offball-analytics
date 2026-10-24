# Databricks notebook source
# MAGIC %run ./00_gold_runtime_config
# MAGIC %run ./01_gold_helpers
# MAGIC %run ./04_aggregate_helpers


if __name__ == "__main__":
    build_count_mart(
        GOLD_CONFIG, "event", "participant", "match", "participant_metrics",
        ("fixture_id", "participant_id", "franchise_id"), "participant_involvement"
    )
