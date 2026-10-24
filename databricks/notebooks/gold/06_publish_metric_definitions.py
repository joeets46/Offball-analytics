# Databricks notebook source
# MAGIC %run ./00_gold_runtime_config
# MAGIC %run ./02_metric_registry_helpers


def main():
    config = GOLD_CONFIG
    definitions = (
        ("space_observation_rate", "Space observation rate", "observed / eligible", "eligible opportunities"),
        ("space_conversion_rate", "Space conversion rate", "successful / observed", "observed opportunities"),
        ("press_positive_outcome_rate", "Press positive outcome rate", "positive outcomes / opportunities", "pressing opportunities"),
        ("press_recovery_rate", "Press recovery rate", "recoveries / opportunities", "pressing opportunities"),
        ("attribution_share", "Attribution share", "attributed share / opportunities", "attributed opportunities"),
    )
    for metric in definitions:
        register_metric(config, *metric)


if __name__ == "__main__":
    main()
