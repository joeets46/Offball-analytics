# Databricks notebook source
"""Shared runtime configuration for Sprint 1 Bronze notebooks.

This notebook is intended to be included with ``%run``. It contains no
source-specific ingestion logic and never reads secret values into logs.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Optional


_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _widget_value(name: str, default: Optional[str] = None) -> Optional[str]:
    try:
        widgets = dbutils.widgets  # type: ignore[name-defined]
    except NameError:
        value = default
    else:
        value = widgets.get(name)
    if value is None:
        return None
    value = value.strip()
    return value if value else default


def _required_widget(name: str) -> str:
    value = _widget_value(name)
    if not value:
        raise ValueError("Required notebook parameter is missing: %s" % name)
    return value


def validate_identifier(value: str, name: str) -> str:
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError("Invalid %s identifier: %s" % (name, value))
    return value


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class RuntimeConfig:
    catalog: str
    bronze_schema: str
    bronze_root_uri: str
    quarantine_root_uri: str
    checkpoint_root_uri: str
    schema_registry_root_uri: str
    source_secret_scope: Optional[str]
    run_mode: str
    ingestion_id: Optional[str]
    snapshot_id: Optional[str]
    source_system_code: Optional[str]
    source_object_name: Optional[str]
    source_version: Optional[str]
    source_domain: Optional[str]
    expected_record_count: Optional[int]

    @property
    def bronze_database(self) -> str:
        return "%s.%s" % (
            validate_identifier(self.catalog, "catalog"),
            validate_identifier(self.bronze_schema, "bronze_schema"),
        )

    def table_name(self, table: str) -> str:
        return "%s.%s" % (self.bronze_database, validate_identifier(table, "table"))


def _optional_int(name: str) -> Optional[int]:
    value = _widget_value(name)
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError("Notebook parameter %s must be an integer" % name) from exc
    if parsed < 0:
        raise ValueError("Notebook parameter %s must be non-negative" % name)
    return parsed


def load_runtime_config() -> RuntimeConfig:
    config = RuntimeConfig(
        catalog=validate_identifier(_required_widget("catalog"), "catalog"),
        bronze_schema=validate_identifier(
            _widget_value("bronze_schema", "bronze") or "bronze",
            "bronze_schema",
        ),
        bronze_root_uri=_required_widget("bronze_root_uri"),
        quarantine_root_uri=_required_widget("quarantine_root_uri"),
        checkpoint_root_uri=_widget_value("checkpoint_root_uri", "") or "",
        schema_registry_root_uri=_widget_value("schema_registry_root_uri", "") or "",
        source_secret_scope=_widget_value("source_secret_scope"),
        run_mode=_widget_value("run_mode", "incremental") or "incremental",
        ingestion_id=_widget_value("ingestion_id"),
        snapshot_id=_widget_value("snapshot_id"),
        source_system_code=_widget_value("source_system_code"),
        source_object_name=_widget_value("source_object_name"),
        source_version=_widget_value("source_version"),
        source_domain=_widget_value("source_domain"),
        expected_record_count=_optional_int("expected_record_count"),
    )
    if config.run_mode not in {"batch", "incremental", "replay"}:
        raise ValueError("run_mode must be batch, incremental, or replay")
    return config


def get_logger(name: str):
    import logging

    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def configure_spark(spark_session) -> None:
    spark_session.conf.set("spark.sql.session.timeZone", "UTC")
    spark_session.conf.set("spark.databricks.delta.schema.autoMerge.enabled", "false")


try:
    RUNTIME_CONFIG = load_runtime_config()
    LOGGER = get_logger("offball.sprint1.runtime")
    configure_spark(spark)  # type: ignore[name-defined]
    LOGGER.info(
        "Runtime configured catalog=%s schema=%s run_mode=%s",
        RUNTIME_CONFIG.catalog,
        RUNTIME_CONFIG.bronze_schema,
        RUNTIME_CONFIG.run_mode,
    )
except NameError:
    # Allows static tooling to parse the notebook outside a Databricks session.
    RUNTIME_CONFIG = None
    LOGGER = get_logger("offball.sprint1.runtime")
