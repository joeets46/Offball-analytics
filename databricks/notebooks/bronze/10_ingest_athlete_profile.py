# Databricks notebook source
# MAGIC %run ../common/00_runtime_config
# MAGIC %run ../common/01_ingestion_helpers

from typing import Dict


def _get(name: str, default=None):
    try:
        widgets = dbutils.widgets  # type: ignore[name-defined]
    except NameError:
        value = default
    else:
        value = widgets.get(name)
    return value.strip() if isinstance(value, str) and value.strip() else default


def main() -> Dict[str, int]:
    source_path = _get(
        "source_path",
        "%s/incoming/athlete/athlete_profile" % RUNTIME_CONFIG.bronze_root_uri.rstrip("/"),
    )
    source_format = _get("source_format", "json")
    result = ingest_source_to_bronze(
        RUNTIME_CONFIG,
        source_path,
        source_format,
        "athlete_profile_raw",
        _get(
            "source_system_code",
            RUNTIME_CONFIG.source_system_code,
        ),
        _get("source_object_name", "athlete_profile"),
        _get("source_version", RUNTIME_CONFIG.source_version),
        ("athlete_profile_id", "athlete_id", "provider_athlete_id"),
        ("updated_timestamp", "source_event_timestamp"),
        ("source_system_code", "ingestion_date"),
        (("athlete_profile_id", "athlete_id", "provider_athlete_id"),),
        None,
    )
    publish_ingestion_metrics(result)
    LOGGER.info("Completed athlete profile Bronze ingestion result=%s", result)
    return result


if __name__ == "__main__":
    main()
