# Databricks notebook source
# MAGIC %run ../common/00_runtime_config
# MAGIC %run ../common/01_ingestion_helpers


def _get(name: str, default=None):
    try:
        widgets = dbutils.widgets  # type: ignore[name-defined]
    except NameError:
        value = default
    else:
        value = widgets.get(name)
    return value.strip() if isinstance(value, str) and value.strip() else default


def main():
    source_path = _get(
        "source_path",
        "%s/incoming/event/fixture" % RUNTIME_CONFIG.bronze_root_uri.rstrip("/"),
    )
    source_format = _get("source_format", "json")
    result = ingest_source_to_bronze(
        RUNTIME_CONFIG,
        source_path,
        source_format,
        "fixture_raw",
        _get(
            "source_system_code",
            RUNTIME_CONFIG.source_system_code,
        ),
        _get("source_object_name", "fixture"),
        _get("source_version", RUNTIME_CONFIG.source_version),
        ("fixture_id", "provider_fixture_id"),
        ("actual_start_timestamp", "event_date", "source_event_timestamp"),
        ("event_date", "ingestion_date"),
        (("fixture_id", "provider_fixture_id"), ("event_date",)),
        None,
    )
    publish_ingestion_metrics(result)
    LOGGER.info("Completed fixture Bronze ingestion result=%s", result)
    return result


if __name__ == "__main__":
    main()
