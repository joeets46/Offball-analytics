# Databricks notebook source
"""UTC and interval validation helpers for Silver."""

from pyspark.sql import functions as F


def validate_interval(dataframe, start_column: str, end_column: str, reason: str):
    invalid = (
        F.col(start_column).isNull()
        | (
            F.col(end_column).isNotNull()
            & (F.col(end_column) < F.col(start_column))
        )
    )
    return dataframe.withColumn(
        "_quality_reason",
        F.when(invalid, F.lit(reason)).otherwise(F.col("_quality_reason")),
    )


def utc_timestamp(dataframe, source_column: str, target_column: str):
    return dataframe.withColumn(
        target_column,
        F.to_utc_timestamp(F.to_timestamp(F.col(source_column)), "UTC"),
    )
