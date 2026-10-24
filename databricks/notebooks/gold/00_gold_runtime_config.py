# Databricks notebook source
"""Runtime configuration shared by Sprint 3 Gold notebooks."""

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
        raise ValueError("Required Gold parameter is missing: %s" % name)
    return value


def _identifier(value: str, name: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError("Invalid %s identifier: %s" % (name, value))
    return value


@dataclass(frozen=True)
class GoldConfig:
    catalog: str
    silver_schema: str
    gold_schema: str
    run_mode: str
    calculation_run_id: str
    metric_version: str
    evaluation_window_type: str
    evaluation_window_start: Optional[str]
    evaluation_window_end: Optional[str]
    minimum_sample_size: int

    @property
    def silver_database(self) -> str:
        return "%s.%s" % (self.catalog, self.silver_schema)

    def silver_table(self, domain: str, table: str) -> str:
        return "%s.%s.%s" % (
            self.catalog,
            _identifier(domain, "Silver domain"),
            _identifier(table, "Silver table"),
        )

    def gold_table(self, domain: str, table: str) -> str:
        return "%s.%s.%s" % (
            self.catalog,
            _identifier(domain, "Gold domain"),
            _identifier(table, "Gold table"),
        )


def load_gold_config() -> GoldConfig:
    run_mode = _widget("run_mode", "incremental") or "incremental"
    if run_mode not in {"batch", "incremental", "replay"}:
        raise ValueError("run_mode must be batch, incremental, or replay")
    run_id = _widget("calculation_run_id")
    if not run_id:
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    minimum = int(_widget("minimum_sample_size", "1") or "1")
    if minimum < 1:
        raise ValueError("minimum_sample_size must be positive")
    return GoldConfig(
        catalog=_identifier(_required("catalog"), "catalog"),
        silver_schema=_identifier(_widget("silver_schema", "silver") or "silver", "silver_schema"),
        gold_schema=_identifier(_widget("gold_schema", "gold") or "gold", "gold_schema"),
        run_mode=run_mode,
        calculation_run_id=run_id,
        metric_version=_required("metric_version"),
        evaluation_window_type=_widget("evaluation_window_type", "all_time") or "all_time",
        evaluation_window_start=_widget("evaluation_window_start"),
        evaluation_window_end=_widget("evaluation_window_end"),
        minimum_sample_size=minimum,
    )


GOLD_CONFIG = load_gold_config()
