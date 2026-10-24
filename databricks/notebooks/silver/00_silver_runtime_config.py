# Databricks notebook source
"""Runtime configuration shared by Sprint 2 Silver notebooks."""

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Optional


_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _widget(name: str, default: Optional[str] = None) -> Optional[str]:
    try:
        value = dbutils.widgets.get(name)  # type: ignore[name-defined]
    except NameError:
        value = default
    if value is None:
        return default
    value = value.strip()
    return value or default


def _required(name: str) -> str:
    value = _widget(name)
    if not value:
        raise ValueError("Required Silver parameter is missing: %s" % name)
    return value


def _identifier(value: str, name: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError("Invalid %s identifier: %s" % (name, value))
    return value


@dataclass(frozen=True)
class SilverConfig:
    catalog: str
    bronze_schema: str
    silver_schema: str
    run_mode: str
    source_snapshot_id: Optional[str]
    ingestion_attempt_id: Optional[str]
    transformation_run_id: str
    quality_root_uri: str
    source_system_precedence: str

    @property
    def bronze_database(self) -> str:
        return "%s.%s" % (self.catalog, self.bronze_schema)

    @property
    def silver_database(self) -> str:
        return "%s.%s" % (self.catalog, self.silver_schema)

    def bronze_table(self, name: str) -> str:
        return "%s.%s" % (self.bronze_database, _identifier(name, "Bronze table"))

    def silver_table(self, domain: str, name: str) -> str:
        return "%s.%s.%s" % (
            self.catalog,
            _identifier(domain, "Silver domain"),
            _identifier(name, "Silver table"),
        )


def load_silver_config() -> SilverConfig:
    run_mode = _widget("run_mode", "incremental") or "incremental"
    if run_mode not in {"batch", "incremental", "replay"}:
        raise ValueError("run_mode must be batch, incremental, or replay")
    transformation_run_id = _widget("transformation_run_id")
    if not transformation_run_id:
        transformation_run_id = datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
    return SilverConfig(
        catalog=_identifier(_required("catalog"), "catalog"),
        bronze_schema=_identifier(_widget("bronze_schema", "bronze") or "bronze", "bronze_schema"),
        silver_schema=_identifier(_widget("silver_schema", "silver") or "silver", "silver_schema"),
        run_mode=run_mode,
        source_snapshot_id=_widget("source_snapshot_id"),
        ingestion_attempt_id=_widget("ingestion_attempt_id"),
        transformation_run_id=transformation_run_id,
        quality_root_uri=_required("quality_root_uri"),
        source_system_precedence=_widget("source_system_precedence", "") or "",
    )


SILVER_CONFIG = load_silver_config()
