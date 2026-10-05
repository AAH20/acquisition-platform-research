"""Tests for data pipeline module."""
import pytest

from acquisition_platform.data_pipeline import (
    DataPipeline,
    PipelineResult,
    PipelineStage,
)


class TestPipelineStage:
    """Tests for PipelineStage dataclass."""

    def test_creation(self):
        stage = PipelineStage(name="extract", stage_type="ingestion", config={}, status="pending")
        assert stage.name == "extract"
        assert stage.stage_type == "ingestion"
        assert stage.config == {}
        assert stage.status == "pending"

    def test_default_status(self):
        stage = PipelineStage(name="t", stage_type="transform", config={})
        assert stage.status == "pending"


class TestPipelineResult:
    """Tests for PipelineResult dataclass."""

    def test_creation(self):
        stages = [PipelineStage(name="s1", stage_type="ingestion", config={}, status="completed")]
        result = PipelineResult(stages=stages, records_processed=10, errors=0, duration_seconds=1.5)
        assert result.stages == stages
        assert result.records_processed == 10
        assert result.errors == 0
        assert result.duration_seconds == 1.5

    def test_defaults(self):
        result = PipelineResult()
        assert result.stages == []
        assert result.records_processed == 0
        assert result.errors == 0
        assert result.duration_seconds == 0.0


class TestDataPipelineCreation:
    """Tests for pipeline creation."""

    def test_pipeline_creation(self):
        pipeline = DataPipeline()
        assert pipeline is not None
        assert pipeline.stages == []

    def test_pipeline_with_name(self):
        pipeline = DataPipeline(name="test_pipeline")
        assert pipeline.name == "test_pipeline"


class TestAddStage:
    """Tests for add_stage method."""

    def test_add_stage(self):
        pipeline = DataPipeline()
        stage = pipeline.add_stage("extract", "ingestion", {"source": "db"})
        assert isinstance(stage, PipelineStage)
        assert stage.name == "extract"
        assert stage.stage_type == "ingestion"
        assert stage.config == {"source": "db"}
        assert len(pipeline.stages) == 1

    def test_add_multiple_stages(self):
        pipeline = DataPipeline()
        pipeline.add_stage("extract", "ingestion", {})
        pipeline.add_stage("transform", "transformation", {})
        pipeline.add_stage("load", "loading", {})
        assert len(pipeline.stages) == 3


class TestIngestData:
    """Tests for ingest_data method."""

    def test_data_ingestion(self):
        pipeline = DataPipeline()
        data = pipeline.ingest_data("test_source", "json")
        assert isinstance(data, list)
        assert len(data) > 0

    def test_ingest_from_dict_source(self):
        pipeline = DataPipeline()
        source = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        data = pipeline.ingest_data(source, "json")
        assert len(data) == 2
        assert data[0]["name"] == "Alice"

    def test_ingest_from_list_source(self):
        pipeline = DataPipeline()
        source = [{"x": 1}, {"x": 2}, {"x": 3}]
        data = pipeline.ingest_data(source, "json")
        assert len(data) == 3

    def test_ingest_empty_list(self):
        pipeline = DataPipeline()
        data = pipeline.ingest_data([], "json")
        assert data == []

    def test_ingest_invalid_format_raises(self):
        pipeline = DataPipeline()
        with pytest.raises(ValueError):
            pipeline.ingest_data("source", "invalid_format")


class TestTransformData:
    """Tests for transform_data method."""

    def test_data_transformation(self):
        pipeline = DataPipeline()
        data = [{"name": "alice", "age": 30}, {"name": "bob", "age": 25}]
        rules = {"uppercase": ["name"]}
        result = pipeline.transform_data(data, rules)
        assert len(result) == 2
        assert result[0]["name"] == "ALICE"
        assert result[1]["name"] == "BOB"

    def test_transform_with_rename(self):
        pipeline = DataPipeline()
        data = [{"old_name": "value"}]
        rules = {"rename": {"old_name": "new_name"}}
        result = pipeline.transform_data(data, rules)
        assert "new_name" in result[0]
        assert "old_name" not in result[0]

    def test_transform_with_filter(self):
        pipeline = DataPipeline()
        data = [{"x": 1}, {"x": 2}, {"x": 3}]
        rules = {"filter": lambda r: r["x"] > 1}
        result = pipeline.transform_data(data, rules)
        assert len(result) == 2

    def test_transform_empty_data(self):
        pipeline = DataPipeline()
        result = pipeline.transform_data([], {"uppercase": ["name"]})
        assert result == []

    def test_transform_no_rules(self):
        pipeline = DataPipeline()
        data = [{"a": 1}]
        result = pipeline.transform_data(data, {})
        assert result == data


class TestValidateData:
    """Tests for validate_data method."""

    def test_pipeline_validation(self):
        pipeline = DataPipeline()
        data = [{"name": "Alice", "age": 30}]
        schema = {"name": str, "age": int}
        assert pipeline.validate_data(data, schema) is True

    def test_validate_fails_on_wrong_type(self):
        pipeline = DataPipeline()
        data = [{"name": "Alice", "age": "thirty"}]
        schema = {"name": str, "age": int}
        assert pipeline.validate_data(data, schema) is False

    def test_validate_fails_on_missing_field(self):
        pipeline = DataPipeline()
        data = [{"name": "Alice"}]
        schema = {"name": str, "age": int}
        assert pipeline.validate_data(data, schema) is False

    def test_validate_empty_data(self):
        pipeline = DataPipeline()
        assert pipeline.validate_data([], {"name": str}) is True

    def test_validate_empty_schema(self):
        pipeline = DataPipeline()
        data = [{"any": "thing"}]
        assert pipeline.validate_data(data, {}) is True


class TestExecutePipeline:
    """Tests for execute_pipeline method."""

    def test_pipeline_execution(self):
        pipeline = DataPipeline()
        pipeline.add_stage("extract", "ingestion", {})
        pipeline.add_stage("transform", "transformation", {})
        data = [{"x": 1}, {"x": 2}]
        result = pipeline.execute_pipeline(data)
        assert isinstance(result, PipelineResult)
        assert result.records_processed == 2
        assert result.errors == 0
        assert result.duration_seconds >= 0.0
        assert len(result.stages) == 2

    def test_execute_empty_pipeline(self):
        pipeline = DataPipeline()
        result = pipeline.execute_pipeline([{"x": 1}])
        assert isinstance(result, PipelineResult)
        assert result.records_processed == 1
        assert result.stages == []

    def test_execute_with_empty_data(self):
        pipeline = DataPipeline()
        pipeline.add_stage("extract", "ingestion", {})
        result = pipeline.execute_pipeline([])
        assert result.records_processed == 0

    def test_stage_status_updated_after_execution(self):
        pipeline = DataPipeline()
        pipeline.add_stage("extract", "ingestion", {})
        pipeline.execute_pipeline([{"x": 1}])
        assert pipeline.stages[0].status == "completed"


class TestEmptyPipeline:
    """Tests for empty pipeline behavior."""

    def test_empty_pipeline(self):
        pipeline = DataPipeline()
        result = pipeline.execute_pipeline([])
        assert isinstance(result, PipelineResult)
        assert result.stages == []
        assert result.records_processed == 0
        assert result.errors == 0
        assert result.duration_seconds >= 0.0

    def test_empty_pipeline_monitor(self):
        pipeline = DataPipeline()
        result = pipeline.execute_pipeline([])
        monitor = pipeline.monitor_pipeline(result)
        assert isinstance(monitor, dict)
        assert monitor["status"] == "success"

    def test_empty_pipeline_report(self):
        pipeline = DataPipeline()
        result = pipeline.execute_pipeline([])
        report = pipeline.generate_pipeline_report(result)
        assert isinstance(report, dict)
        assert report["total_stages"] == 0


class TestMonitorPipeline:
    """Tests for monitor_pipeline method."""

    def test_pipeline_monitoring(self):
        pipeline = DataPipeline()
        pipeline.add_stage("extract", "ingestion", {})
        result = pipeline.execute_pipeline([{"x": 1}])
        monitor = pipeline.monitor_pipeline(result)
        assert isinstance(monitor, dict)
        assert "status" in monitor
        assert "records_processed" in monitor
        assert "errors" in monitor
        assert "duration_seconds" in monitor
        assert monitor["records_processed"] == 1

    def test_monitor_with_errors(self):
        pipeline = DataPipeline()
        result = PipelineResult(stages=[], records_processed=0, errors=2, duration_seconds=0.5)
        monitor = pipeline.monitor_pipeline(result)
        assert monitor["status"] == "failed"
        assert monitor["errors"] == 2

    def test_monitor_success_status(self):
        pipeline = DataPipeline()
        result = PipelineResult(stages=[], records_processed=5, errors=0, duration_seconds=1.0)
        monitor = pipeline.monitor_pipeline(result)
        assert monitor["status"] == "success"


class TestOptimizePipeline:
    """Tests for optimize_pipeline method."""

    def test_pipeline_optimization(self):
        pipeline = DataPipeline()
        stages = [
            PipelineStage(name="s1", stage_type="ingestion", config={}, status="completed"),
            PipelineStage(name="s2", stage_type="transformation", config={}, status="completed"),
        ]
        optimized = pipeline.optimize_pipeline(stages)
        assert isinstance(optimized, list)
        assert len(optimized) == 2
        assert all(isinstance(s, PipelineStage) for s in optimized)

    def test_optimize_empty_stages(self):
        pipeline = DataPipeline()
        optimized = pipeline.optimize_pipeline([])
        assert optimized == []

    def test_optimize_sorts_by_name(self):
        pipeline = DataPipeline()
        stages = [
            PipelineStage(name="z_stage", stage_type="ingestion", config={}),
            PipelineStage(name="a_stage", stage_type="ingestion", config={}),
        ]
        optimized = pipeline.optimize_pipeline(stages)
        assert optimized[0].name == "a_stage"
        assert optimized[1].name == "z_stage"


class TestGenerateReport:
    """Tests for generate_pipeline_report method."""

    def test_pipeline_report(self):
        pipeline = DataPipeline()
        pipeline.add_stage("extract", "ingestion", {})
        pipeline.add_stage("transform", "transformation", {})
        result = pipeline.execute_pipeline([{"x": 1}, {"x": 2}])
        report = pipeline.generate_pipeline_report(result)
        assert isinstance(report, dict)
        assert "total_stages" in report
        assert "records_processed" in report
        assert "errors" in report
        assert "duration_seconds" in report
        assert "stages" in report
        assert report["total_stages"] == 2
        assert report["records_processed"] == 2

    def test_report_with_errors(self):
        pipeline = DataPipeline()
        result = PipelineResult(stages=[], records_processed=0, errors=3, duration_seconds=0.1)
        report = pipeline.generate_pipeline_report(result)
        assert report["errors"] == 3
        assert report["status"] == "failed"

    def test_report_stage_details(self):
        pipeline = DataPipeline()
        pipeline.add_stage("extract", "ingestion", {})
        result = pipeline.execute_pipeline([{"x": 1}])
        report = pipeline.generate_pipeline_report(result)
        assert len(report["stages"]) == 1
        assert report["stages"][0]["name"] == "extract"


class TestErrorHandling:
    """Tests for error handling."""

    def test_pipeline_error_handling(self):
        pipeline = DataPipeline()
        with pytest.raises(ValueError):
            pipeline.ingest_data("source", "unsupported_format")

    def test_transform_with_invalid_rules(self):
        pipeline = DataPipeline()
        data = [{"x": 1}]
        result = pipeline.transform_data(data, {"unknown_rule": True})
        assert result == data

    def test_execute_with_none_data(self):
        pipeline = DataPipeline()
        result = pipeline.execute_pipeline([])
        assert result.records_processed == 0

    def test_add_stage_invalid_type(self):
        pipeline = DataPipeline()
        with pytest.raises(ValueError):
            pipeline.add_stage("bad", "unknown_type", {})
