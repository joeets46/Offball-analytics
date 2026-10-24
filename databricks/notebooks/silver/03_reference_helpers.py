# Databricks notebook source
"""Conformed-key lookup and unresolved-reference helpers."""

from pyspark.sql import functions as F


def require_reference(
    dataframe,
    reference_dataframe,
    source_column: str,
    target_column: str,
    reason: str,
):
    reference = reference_dataframe.select(
        F.col(target_column).alias("_reference_value")
    ).dropDuplicates()
    return (
        dataframe.join(
            reference,
            dataframe[source_column].eqNullSafe(reference["_reference_value"]),
            "left",
        )
        .withColumn(
            "_quality_reason",
            F.when(
                F.col("_reference_value").isNull(),
                F.lit(reason),
            ).otherwise(F.col("_quality_reason")),
        )
        .drop("_reference_value")
    )
