"""Data pipeline module for the acquisition platform.

Provides a configurable multi-stage data pipeline with ingestion,
transformation, validation, execution, monitoring, optimization,
and reporting capabilities.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from acquisition_platform.observability import get_logger

logger = get_logger(__name__)

VALID_STAGE_TYPES = {"ingestion", "transformation", "validation", "loading"}
VALID_FORMATS = {"json", "csv", "yaml", "dict", "list"}


@dataclass
class PipelineStage:
    """Represents a single stage in the data pipeline.

    Attributes:
        name: Human-readable stage name.
        stage_type: Type of stage (ingestion, transformation, validation, loading).
        config: Stage-specific configuration dictionary.
        status: Current status of the stage (pending, running, completed, failed).
    """

    name: str
    stage_type: str
    config: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"


@dataclass
class PipelineResult:
    """Result of a pipeline execution.

    Attributes:
        stages: List of stages that were executed.
        records_processed: Number of records successfully processed.
        errors: Number of errors encountered during execution.
        duration_seconds: Total wall-clock execution time.
    """

    stages: list[PipelineStage] = field(default_factory=list)
    records_processed: int = 0
    errors: int = 0
    duration_seconds: float = 0.0


class DataPipeline:
    """Configurable multi-stage data pipeline.

    Supports adding stages, ingesting data from various sources,
    transforming data with rules, validating against schemas,
    executing the full pipeline, monitoring results, optimizing
    stage ordering, and generating reports.
    """

    def __init__(self, name: str = "default") -> None:
        """Initialize the pipeline.

        Args:
            name: Human-readable pipeline name.
        """
        self.name = name
        self.stages: list[PipelineStage] = []

    def add_stage(
        self, name: str, stage_type: str, config: dict[str, Any] | None = None
    ) -> PipelineStage:
        """Add a stage to the pipeline.

        Args:
            name: Stage name.
            stage_type: Stage type (ingestion, transformation, validation, loading).
            config: Optional stage configuration.

        Returns:
            The created PipelineStage.

        Raises:
            ValueError: If stage_type is not a valid type.
        """
        if stage_type not in VALID_STAGE_TYPES:
            raise ValueError(
                f"Invalid stage_type '{stage_type}'. Must be one of {VALID_STAGE_TYPES}"
            )
        stage = PipelineStage(
            name=name, stage_type=stage_type, config=config or {}, status="pending"
        )
        self.stages.append(stage)
        logger.debug("Added stage '%s' (type=%s) to pipeline '%s'", name, stage_type, self.name)
        return stage

    def ingest_data(self, source: Any, format: str) -> list[dict[str, Any]]:
        """Ingest data from a source.

        Args:
            source: Data source (list of dicts, dict, or string identifier).
            format: Data format (json, csv, yaml, dict, list).

        Returns:
            List of dictionaries representing the ingested data.

        Raises:
            ValueError: If format is not supported.
        """
        if format not in VALID_FORMATS:
            raise ValueError(f"Unsupported format '{format}'. Must be one of {VALID_FORMATS}")

        if isinstance(source, list):
            return [dict(item) for item in source]
        if isinstance(source, dict):
            return [dict(source)]
        if isinstance(source, str):
            # Simulate ingesting from a string source identifier
            return [{"source": source, "data": f"ingested_from_{source}"}]
        return []

    def transform_data(
        self, data: list[dict[str, Any]], rules: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Transform data according to rules.

        Supported rules:
            - "uppercase": list of field names to uppercase.
            - "lowercase": list of field names to lowercase.
            - "rename": dict mapping old field names to new names.
            - "filter": callable that returns True for rows to keep.
            - "default": dict of field_name -> default_value for missing fields.

        Args:
            data: Input data as list of dicts.
            rules: Transformation rules.

        Returns:
            Transformed data.
        """
        result = [dict(row) for row in data]

        if "filter" in rules:
            predicate = rules["filter"]
            if callable(predicate):
                result = [row for row in result if predicate(row)]

        if "uppercase" in rules:
            for row in result:
                for field_name in rules["uppercase"]:
                    if field_name in row and isinstance(row[field_name], str):
                        row[field_name] = row[field_name].upper()

        if "lowercase" in rules:
            for row in result:
                for field_name in rules["lowercase"]:
                    if field_name in row and isinstance(row[field_name], str):
                        row[field_name] = row[field_name].lower()

        if "rename" in rules:
            rename_map = rules["rename"]
            for row in result:
                for old_name, new_name in rename_map.items():
                    if old_name in row:
                        row[new_name] = row.pop(old_name)

        if "default" in rules:
            defaults = rules["default"]
            for row in result:
                for field_name, default_value in defaults.items():
                    if field_name not in row:
                        row[field_name] = default_value

        return result

    def validate_data(
        self, data: list[dict[str, Any]], schema: dict[str, type]
    ) -> bool:
        """Validate data against a schema.

        Args:
            data: Data to validate.
            schema: Schema mapping field names to expected types.

        Returns:
            True if all records match the schema, False otherwise.
        """
        for row in data:
            for field_name, expected_type in schema.items():
                if field_name not in row:
                    return False
                if not isinstance(row[field_name], expected_type):
                    return False
        return True

    def execute_pipeline(self, data: list[dict[str, Any]]) -> PipelineResult:
        """Execute the pipeline on the given data.

        Args:
            data: Input data to process.

        Returns:
            PipelineResult with execution details.
        """
        start_time = time.perf_counter()
        current_data = [dict(row) for row in data]
        errors = 0

        for stage in self.stages:
            stage.status = "running"
            try:
                if stage.stage_type == "ingestion":
                    # Ingestion stages pass data through (already ingested)
                    pass
                elif stage.stage_type == "transformation":
                    current_data = self.transform_data(current_data, stage.config)
                elif stage.stage_type == "validation":
                    if not self.validate_data(current_data, stage.config):
                        errors += 1
                        stage.status = "failed"
                        continue
                elif stage.stage_type == "loading":
                    # Loading stages pass data through
                    pass
                stage.status = "completed"
            except Exception as exc:
                logger.error("Stage '%s' failed: %s", stage.name, exc)
                stage.status = "failed"
                errors += 1

        duration = time.perf_counter() - start_time
        return PipelineResult(
            stages=list(self.stages),
            records_processed=len(current_data),
            errors=errors,
            duration_seconds=duration,
        )

    def monitor_pipeline(self, result: PipelineResult) -> dict[str, Any]:
        """Monitor a pipeline execution result.

        Args:
            result: The PipelineResult to monitor.

        Returns:
            Dictionary with monitoring metrics.
        """
        status = "success" if result.errors == 0 else "failed"
        return {
            "status": status,
            "records_processed": result.records_processed,
            "errors": result.errors,
            "duration_seconds": result.duration_seconds,
            "stages_total": len(result.stages),
            "stages_completed": sum(1 for s in result.stages if s.status == "completed"),
            "stages_failed": sum(1 for s in result.stages if s.status == "failed"),
        }

    def optimize_pipeline(
        self, stages: list[PipelineStage]
    ) -> list[PipelineStage]:
        """Optimize pipeline stage ordering.

        Sorts stages alphabetically by name for deterministic execution.

        Args:
            stages: List of stages to optimize.

        Returns:
            Optimized list of stages.
        """
        return sorted(stages, key=lambda s: s.name)

    def generate_pipeline_report(self, result: PipelineResult) -> dict[str, Any]:
        """Generate a report from a pipeline execution result.

        Args:
            result: The PipelineResult to report on.

        Returns:
            Dictionary with report data.
        """
        status = "success" if result.errors == 0 else "failed"
        return {
            "pipeline_name": self.name,
            "status": status,
            "total_stages": len(result.stages),
            "records_processed": result.records_processed,
            "errors": result.errors,
            "duration_seconds": result.duration_seconds,
            "stages": [
                {
                    "name": s.name,
                    "type": s.stage_type,
                    "status": s.status,
                }
                for s in result.stages
            ],
        }
