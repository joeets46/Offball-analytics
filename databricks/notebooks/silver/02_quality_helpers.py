# Databricks notebook source
"""Silver data-quality and reconciliation helpers."""

from pyspark.sql import functions as F
from pyspark.sql import types as T


def quality_records(
    dataframe,
    table_name: str,
    rule_code: str,
    severity: str,
    reason_column: str = "_quality_reason",
):
    return (
        dataframe.where(F.col(reason_column).isNotNull())
        .select(
            F.sha2(
                F.concat_ws(
                    "|",
                    F.lit(table_name),
                    F.col("source_snapshot_id"),
                    F.col("ingestion_attempt_id"),
                    F.col("bronze_payload_hash"),
                    F.lit(rule_code),
                ),
                256,
            ).alias("quality_record_id"),
            F.lit(table_name).alias("table_name"),
            F.lit(rule_code).alias("rule_code"),
            F.lit(severity).alias("severity"),
            F.lit("quarantined").alias("quality_status"),
            F.col(reason_column).alias("quality_reason"),
            "source_snapshot_id",
            "ingestion_attempt_id",
            "transformation_run_id",
            F.current_timestamp().alias("detected_at"),
        )
    )


def write_quality_records(dataframe, config, table_name: str, rule_code: str, severity: str):
    if dataframe.rdd.isEmpty():
        return 0
    target = "%s._quality_record" % config.silver_database
    records = quality_records(dataframe, table_name, rule_code, severity)
    records.write.format("delta").mode("append").saveAsTable(target)
    return records.count()


def assert_no_invalid_rows(dataframe, required_columns, table_name: str):
    invalid = None
    for column in required_columns:
        condition = F.col(column).isNull()
        invalid = condition if invalid is None else invalid | condition
    if dataframe.where(invalid).limit(1).count():
        raise ValueError("Required Silver fields are invalid: %s" % table_name)


def ensure_operational_outputs(config):
    definitions = {
        "_quality_run": T.StructType([
            T.StructField("quality_run_id", T.StringType(), False),
            T.StructField("transformation_run_id", T.StringType(), False),
            T.StructField("table_name", T.StringType(), False),
            T.StructField("input_count", T.LongType(), False),
            T.StructField("invalid_count", T.LongType(), False),
            T.StructField("warning_count", T.LongType(), False),
            T.StructField("status", T.StringType(), False),
            T.StructField("created_at", T.TimestampType(), False),
        ]),
        "_reconciliation_conflict": T.StructType([
            T.StructField("conflict_id", T.StringType(), False),
            T.StructField("table_name", T.StringType(), False),
            T.StructField("business_key", T.StringType(), False),
            T.StructField("selected_payload_hash", T.StringType(), True),
            T.StructField("candidate_count", T.LongType(), False),
            T.StructField("resolution_status", T.StringType(), False),
            T.StructField("transformation_run_id", T.StringType(), False),
            T.StructField("created_at", T.TimestampType(), False),
        ]),
        "_unresolved_reference": T.StructType([
            T.StructField("unresolved_reference_id", T.StringType(), False),
            T.StructField("table_name", T.StringType(), False),
            T.StructField("reference_type", T.StringType(), False),
            T.StructField("reference_value", T.StringType(), True),
            T.StructField("reason", T.StringType(), False),
            T.StructField("source_snapshot_id", T.StringType(), True),
            T.StructField("ingestion_attempt_id", T.StringType(), True),
            T.StructField("transformation_run_id", T.StringType(), False),
            T.StructField("created_at", T.TimestampType(), False),
        ]),
        "_transformation_run": T.StructType([
            T.StructField("transformation_run_id", T.StringType(), False),
            T.StructField("run_mode", T.StringType(), False),
            T.StructField("status", T.StringType(), False),
            T.StructField("started_at", T.TimestampType(), False),
            T.StructField("completed_at", T.TimestampType(), True),
        ]),
    }
    for suffix, schema in definitions.items():
        table_name = "%s.%s" % (config.silver_database, suffix)
        if not spark.catalog.tableExists(table_name):  # type: ignore[name-defined]
            spark.createDataFrame([], schema).write.format("delta").mode("overwrite").saveAsTable(table_name)


def write_reconciliation_conflicts(dataframe, config, table_name: str, key_columns):
    grouped = dataframe.groupBy(*key_columns).agg(
        F.count("*").alias("candidate_count"),
        F.max("payload_hash").alias("selected_payload_hash"),
    ).where(F.col("candidate_count") > 1)
    if grouped.rdd.isEmpty():
        return 0
    output = grouped.select(
        F.sha2(F.concat_ws("|", F.lit(table_name), *[F.col(c).cast("string") for c in key_columns]), 256).alias("conflict_id"),
        F.lit(table_name).alias("table_name"),
        F.to_json(F.struct(*[F.col(c) for c in key_columns])).alias("business_key"),
        "selected_payload_hash",
        "candidate_count",
        F.lit("deterministic_precedence_selected").alias("resolution_status"),
        F.lit(config.transformation_run_id).alias("transformation_run_id"),
        F.current_timestamp().alias("created_at"),
    )
    output.write.format("delta").mode("append").saveAsTable(
        "%s._reconciliation_conflict" % config.silver_database
    )
    return output.count()
