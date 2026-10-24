# Databricks notebook source
# MAGIC %run ./00_silver_runtime_config
# MAGIC %run ./01_silver_helpers
# MAGIC %run ./02_quality_helpers

from pyspark.sql import functions as F


SILVER_TABLES = {
    "athlete": ("athlete_profile",),
    "event": (
        "fixture",
        "calendar",
        "tournament",
        "competition_round",
        "type",
        "participant",
        "match_result",
        "scoring_event",
        "event_incident",
    ),
    "analytics": (
        "match_period",
        "match_state_interval",
        "possession_sequence",
        "phase_interval",
        "opportunity",
        "space_opportunity",
        "space_baseline",
        "space_counterfactual",
        "space_outcome",
        "attribution_ledger",
        "pressing_opportunity",
        "press_trigger",
        "press_action",
        "press_support",
        "press_bypass",
        "press_outcome",
        "recovery_action",
    ),
}


COMMON_COLUMNS = {
    "source_system_code",
    "source_record_reference",
    "source_version",
    "source_snapshot_id",
    "ingestion_attempt_id",
    "bronze_payload_hash",
    "silver_record_version",
    "is_current",
    "quality_status",
    "transformation_run_id",
    "transformed_at",
}


def _invalid_lineage(table_name: str):
    table = spark.table(table_name)  # type: ignore[name-defined]
    condition = None
    for column in COMMON_COLUMNS:
        current = F.col(column).isNull()
        condition = current if condition is None else condition | current
    return table.where(condition).count()


def _invalid_confidence(table_name: str):
    table = spark.table(table_name)  # type: ignore[name-defined]
    if "confidence" not in table.columns:
        return 0
    return table.where(
        F.col("confidence").isNotNull()
        & ((F.col("confidence") < 0) | (F.col("confidence") > 1))
    ).count()


def main():
    config = SILVER_CONFIG
    ensure_operational_outputs(config)
    failures = []
    report = []
    for domain, tables in SILVER_TABLES.items():
        for table in tables:
            table_name = config.silver_table(domain, table)
            if not spark.catalog.tableExists(table_name):  # type: ignore[name-defined]
                failures.append("%s:missing_table" % table_name)
                continue
            columns = set(spark.table(table_name).columns)  # type: ignore[name-defined]
            missing = sorted(COMMON_COLUMNS.difference(columns))
            lineage_invalid = _invalid_lineage(table_name) if not missing else -1
            confidence_invalid = _invalid_confidence(table_name)
            report.append(
                (
                    config.transformation_run_id,
                    table_name,
                    len(missing),
                    lineage_invalid,
                    confidence_invalid,
                    "pass" if not missing and lineage_invalid == 0 and confidence_invalid == 0 else "fail",
                )
            )
            if missing:
                failures.append("%s:missing=%s" % (table_name, ",".join(missing)))
            if lineage_invalid:
                failures.append("%s:invalid_lineage=%s" % (table_name, lineage_invalid))
            if confidence_invalid:
                failures.append("%s:invalid_confidence=%s" % (table_name, confidence_invalid))

    schema = "transformation_run_id string, table_name string, missing_column_count long, invalid_lineage_count long, invalid_confidence_count long, status string"
    spark.createDataFrame(report, schema).write.format("delta").mode("append").saveAsTable(
        "%s._quality_run" % config.silver_database
    )
    if failures:
        raise RuntimeError("Silver contract validation failed: %s" % "; ".join(failures))
    print("Silver contract validation passed for %d tables" % len(report))
    return report


if __name__ == "__main__":
    main()
