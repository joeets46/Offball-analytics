# Databricks notebook source
"""Reusable Gold aggregation and exposure helpers."""

from pyspark.sql import functions as F
from pyspark.sql import DataFrame

from typing import Sequence


def available_column(dataframe, candidates, default=None):
    for candidate in candidates:
        if candidate in dataframe.columns:
            return F.col(candidate)
    return F.lit(default)


def aggregate_count(dataframe, group_columns, metric_code, config, row_filter=None):
    source = dataframe.where(row_filter) if row_filter is not None else dataframe
    grouped = source.groupBy(*group_columns).agg(
        F.count("*").alias("metric_numerator"),
        F.count("*").alias("metric_denominator"),
    )
    return add_gold_contract(
        grouped,
        config,
        metric_code,
        F.col("metric_numerator"),
        F.col("metric_denominator"),
    )


def per_90(numerator, minutes):
    return F.when(minutes > 0, numerator * F.lit(90.0) / minutes).otherwise(
        F.lit(None).cast("double")
    )


def build_count_mart(config, source_domain: str, source_table: str,
                     target_domain: str, target_table: str,
                     requested_groups: Sequence[str], metric_code: str) -> dict:
    source = silver_current(config, source_domain, source_table)
    groups = [column for column in requested_groups if column in source.columns]
    if not groups:
        raise RuntimeError(
            "Silver source %s.%s has none of the required Gold grain columns: %s"
            % (source_domain, source_table, ", ".join(requested_groups))
        )
    result = source.groupBy(*groups).agg(
        F.count(F.lit(1)).alias("_numerator"),
        F.count(F.lit(1)).alias("_denominator"),
    )
    result = add_gold_contract(
        result,
        config,
        metric_code,
        F.col("_numerator"),
        F.col("_denominator"),
    ).drop("_numerator", "_denominator")
    result = publish_lineage_columns(result)
    keys = list(groups) + ["metric_code", "metric_version", "evaluation_window_type"]
    metrics = merge_gold(result, config.gold_table(target_domain, target_table), keys)
    publish_metrics(target_table, metrics)
    return metrics
