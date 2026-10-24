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
        "%s/incoming/event/participant" % RUNTIME_CONFIG.bronze_root_uri.rstrip("/"),
    )
    source_format = _get("source_format", "json")
    result = ingest_source_to_bronze(
        RUNTIME_CONFIG,
        source_path,
        source_format,
        "participant_raw",
        _get(
            "source_system_code",
            RUNTIME_CONFIG.source_system_code,
        ),
        _get("source_object_name", "participant"),
        _get("source_version", RUNTIME_CONFIG.source_version),
        ("participant_id", "provider_participant_id"),
        ("participation_timestamp", "updated_timestamp", "source_event_timestamp"),
        ("fixture_id", "ingestion_date"),
        (("participant_id", "provider_participant_id"), ("fixture_id",)),
        None,
    )
    publish_ingestion_metrics(result)
    LOGGER.info("Completed participant Bronze ingestion result=%s", result)
    return result


if __name__ == "__main__":
    main()
