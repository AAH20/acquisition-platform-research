"""Consolidated reporting for the acquisition platform.

Aggregates results from every algorithm module into a single :class:`Report`
and renders it as JSON, CSV, or Markdown. This is the business-facing output
layer: analysts, brokers, and investors export one artifact that combines
matching, valuation, fraud, portfolio, pricing, entity-resolution, ranking,
and evolution outputs.

Design notes
------------
- Sections are stored as ``name -> list[dict]``. Every module result has a
  ``to_dict`` (via :class:`acquisition_platform.serialization.SerializableMixin`),
  so aggregation is uniform regardless of the source type.
- CSV flattens all sections into one table with a leading ``section`` column
  and the union of every row's keys as the remaining columns. Nested values
  (lists/dicts) are JSON-encoded into the cell.
- Markdown emits one table per non-empty section.
"""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Iterable

from acquisition_platform.serialization import _encode

from acquisition_platform.observability import get_logger, log_execution_time, log_module_call

logger = get_logger(__name__)

Sections = dict[str, list[dict[str, Any]]]


def _as_rows(items: Any) -> list[dict[str, Any]]:
    """Normalize a value into a list of plain dicts.

    Accepts a single serializable object, a list of them, or plain dicts.
    """
    if items is None:
        return []
    if isinstance(items, dict):
        return [_encode(items)]
    if isinstance(items, (list, tuple)):
        rows: list[dict[str, Any]] = []
        for item in items:
            if isinstance(item, dict):
                rows.append(_encode(item))
            elif hasattr(item, "to_dict"):
                rows.append(item.to_dict())
            else:  # pragma: no cover - defensive
                rows.append({"value": _encode(item)})
        return rows
    if hasattr(items, "to_dict"):
        return [items.to_dict()]
    return [{"value": _encode(items)}]


def _json_cell(value: Any) -> Any:
    """Render a cell value, JSON-encoding anything non-scalar."""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(_encode(value), sort_keys=True)
    if value is None:
        return ""
    return value


class Report:
    """Aggregates results from all platform modules and exports them.

    Parameters
    ----------
    title:
        Human-readable report title.
    metadata:
        Arbitrary report-level metadata (analyst, run id, timestamp, ...).
    """

    def __init__(
        self,
        title: str = "Acquisition Platform Report",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.title = title
        self.metadata: dict[str, Any] = dict(metadata or {})
        self.sections: Sections = {}

    # -- aggregation --------------------------------------------------------

    @log_execution_time(logger)
    def add_section(self, name: str, items: Any) -> "Report":
        """Append rows to a named section, creating it if necessary."""
        self.sections.setdefault(name, []).extend(_as_rows(items))
        return self

    @log_execution_time(logger)
    def add_matches(self, matches: Any) -> "Report":
        return self.add_section("matches", matches)

    @log_execution_time(logger)
    def add_valuation(self, valuation: Any) -> "Report":
        return self.add_section("valuation", valuation)

    @log_execution_time(logger)
    def add_valuations(self, valuations: Any) -> "Report":
        return self.add_section("valuation", valuations)

    @log_execution_time(logger)
    def add_fraud_scores(self, scores: Any) -> "Report":
        return self.add_section("fraud_scores", scores)

    @log_execution_time(logger)
    def add_portfolio(self, portfolio: Any) -> "Report":
        return self.add_section("portfolio", portfolio)

    @log_execution_time(logger)
    def add_price_recommendation(self, recommendation: Any) -> "Report":
        return self.add_section("price_recommendation", recommendation)

    @log_execution_time(logger)
    def add_entity_clusters(self, clusters: Any) -> "Report":
        return self.add_section("entity_clusters", clusters)

    @log_execution_time(logger)
    def add_ranked_listings(self, listings: Any) -> "Report":
        return self.add_section("ranked_listings", listings)

    @log_execution_time(logger)
    def add_evolution(self, evolution: Any) -> "Report":
        return self.add_section("evolution", evolution)

    # -- export -------------------------------------------------------------

    @log_execution_time(logger)
    def to_dict(self) -> dict[str, Any]:
        """Return the report as a JSON-compatible dict."""
        return {
            "title": self.title,
            "metadata": _encode(self.metadata),
            "sections": {
                name: [_encode(row) for row in rows]
                for name, rows in self.sections.items()
            },
        }

    @log_execution_time(logger)
    def to_json(self, indent: int | None = 2) -> str:
        """Serialize the report to JSON (non-serializable values stringified)."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @log_execution_time(logger)
    def to_csv(self) -> str:
        """Flatten all sections into a single CSV table.

        The first column is ``section``; the remaining columns are the union
        of every row's keys in first-seen order. Nested values are
        JSON-encoded. An empty report yields just the ``section`` header.
        """
        rows: list[dict[str, Any]] = []
        columns: list[str] = []
        seen: set[str] = set()

        for name, section_rows in self.sections.items():
            for row in section_rows:
                for key in row:
                    if key not in seen:
                        seen.add(key)
                        columns.append(key)
                rows.append({"section": name, **row})

        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer, fieldnames=["section", *columns], extrasaction="ignore"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _json_cell(v) for k, v in row.items()})
        return buffer.getvalue()

    @log_execution_time(logger)
    def to_markdown(self) -> str:
        """Render the report as Markdown with one table per non-empty section."""
        lines: list[str] = [f"# {self.title}", ""]

        if self.metadata:
            lines.append("**Metadata**")
            lines.append("")
            for key, value in self.metadata.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        for name, rows in self.sections.items():
            if not rows:
                continue
            heading = name.replace("_", " ").title()
            lines.append(f"## {heading}")
            lines.append("")

            columns: list[str] = []
            seen: set[str] = set()
            for row in rows:
                for key in row:
                    if key not in seen:
                        seen.add(key)
                        columns.append(key)

            lines.append("| " + " | ".join(columns) + " |")
            lines.append("| " + " | ".join("---" for _ in columns) + " |")
            for row in rows:
                cells = [str(_json_cell(row.get(col, ""))) for col in columns]
                lines.append("| " + " | ".join(cells) + " |")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"


def generate_report(
    title: str = "Acquisition Platform Report",
    metadata: dict[str, Any] | None = None,
    matches: Iterable[Any] | None = None,
    valuations: Iterable[Any] | None = None,
    fraud_scores: Iterable[Any] | None = None,
    portfolio: Any | None = None,
    price_recommendation: Any | None = None,
    entity_clusters: Iterable[Any] | None = None,
    ranked_listings: Iterable[Any] | None = None,
    evolution: Any | None = None,
) -> Report:
    """Build a :class:`Report` from arbitrary module results.

    Only the arguments that are provided are added as sections, so callers can
    assemble a partial due-diligence report from whatever engines they ran.
    """
    report = Report(title=title, metadata=metadata)

    if matches is not None:
        report.add_matches(matches)
    if valuations is not None:
        report.add_valuations(valuations)
    if fraud_scores is not None:
        report.add_fraud_scores(fraud_scores)
    if portfolio is not None:
        report.add_portfolio(portfolio)
    if price_recommendation is not None:
        report.add_price_recommendation(price_recommendation)
    if entity_clusters is not None:
        report.add_entity_clusters(entity_clusters)
    if ranked_listings is not None:
        report.add_ranked_listings(ranked_listings)
    if evolution is not None:
        report.add_evolution(evolution)

    return report
