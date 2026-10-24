# Databricks notebook source
# MAGIC %run ./00_gold_runtime_config
# MAGIC %run ./01_gold_helpers
# MAGIC %run ./04_aggregate_helpers


if __name__ == "__main__":
    build_count_mart(
        GOLD_CONFIG, "analytics", "space_opportunity", "team", "space_creation_profile",
        ("franchise_id", "season_id", "space_type"), "space_opportunities"
    )
