# Databricks notebook source
# MAGIC %run ./00_gold_runtime_config
# MAGIC %run ./01_gold_helpers
# MAGIC %run ./04_aggregate_helpers


if __name__ == "__main__":
    build_count_mart(
        GOLD_CONFIG, "analytics", "match_state_interval", "team", "match_summary",
        ("fixture_id", "participant_id", "franchise_id"), "team_match_events"
    )
