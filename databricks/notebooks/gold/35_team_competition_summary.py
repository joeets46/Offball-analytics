# Databricks notebook source
# MAGIC %run ./00_gold_runtime_config
# MAGIC %run ./01_gold_helpers
# MAGIC %run ./04_aggregate_helpers


if __name__ == "__main__":
    build_count_mart(
        GOLD_CONFIG, "event", "fixture", "team", "competition_summary",
        ("franchise_id", "competition_id", "season_id"), "team_fixtures"
    )
