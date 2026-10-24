# Databricks notebook source
# MAGIC %run ./00_gold_runtime_config
# MAGIC %run ./01_gold_helpers
# MAGIC %run ./04_aggregate_helpers


if __name__ == "__main__":
    build_count_mart(
        GOLD_CONFIG, "analytics", "attribution_ledger", "team", "attribution_profile",
        ("franchise_id", "season_id", "attribution_type"), "attribution_events"
    )
