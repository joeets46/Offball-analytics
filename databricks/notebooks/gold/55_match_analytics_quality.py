# Databricks notebook source
# MAGIC %run ./00_gold_runtime_config
# MAGIC %run ./01_gold_helpers
# MAGIC %run ./04_aggregate_helpers


if __name__ == "__main__":
    build_count_mart(
        GOLD_CONFIG, "analytics", "opportunity", "match", "analytics_quality",
        ("fixture_id", "opportunity_type"), "eligible_opportunities"
    )
