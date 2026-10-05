"""Tests for batch processing module."""
import time

import pytest

from acquisition_platform.batch_processing import (
    BatchJob,
    BatchProcessor,
    BatchResult,
)


class TestBatchJob:
    """Tests for BatchJob dataclass."""

    def test_creation(self):
        job = BatchJob(
            job_id="job-001",
            name="test-batch",
            status="pending",
            records=[{"id": 1}, {"id": 2}],
            config={"chunk_size": 10},
        )
        assert job.job_id == "job-001"
        assert job.name == "test-batch"
        assert job.status == "pending"
        assert len(job.records) == 2
        assert job.config["chunk_size"] == 10

    def test_default_status(self):
        job = BatchJob(
            job_id="job-002",
            name="default-status",
            status="pending",
            records=[],
            config={},
        )
        assert job.status == "pending"


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_creation(self):
        job = BatchJob(
            job_id="job-003",
            name="result-test",
            status="completed",
            records=[{"id": 1}],
            config={},
        )
        result = BatchResult(
            job=job,
            processed=1,
            failed=0,
            duration_seconds=0.5,
            errors=[],
        )
        assert result.job is job
        assert result.processed == 1
        assert result.failed == 0
        assert result.duration_seconds == 0.5
        assert result.errors == []

    def test_with_errors(self):
        job = BatchJob(
            job_id="job-004",
            name="error-test",
            status="failed",
            records=[{"id": 1}],
            config={},
        )
        result = BatchResult(
            job=job,
            processed=0,
            failed=1,
            duration_seconds=0.1,
            errors=["record 1 failed"],
        )
        assert result.failed == 1
        assert len(result.errors) == 1


class TestBatchCreation:
    """test_batch_creation: batch created."""

    def test_create_batch(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="import-job",
            records=[{"id": i} for i in range(5)],
            config={"chunk_size": 2},
        )
        assert isinstance(job, BatchJob)
        assert job.name == "import-job"
        assert job.status == "pending"
        assert len(job.records) == 5
        assert job.config["chunk_size"] == 2
        assert job.job_id is not None
        assert len(job.job_id) > 0

    def test_create_batch_generates_unique_ids(self):
        processor = BatchProcessor()
        job1 = processor.create_batch("job1", [], {})
        job2 = processor.create_batch("job2", [], {})
        assert job1.job_id != job2.job_id


class TestBatchExecution:
    """test_batch_execution: batch executed."""

    def test_execute_batch(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="exec-job",
            records=[{"value": i} for i in range(10)],
            config={"chunk_size": 3},
        )
        result = processor.execute_batch(job)
        assert isinstance(result, BatchResult)
        assert result.job is job
        assert result.processed == 10
        assert result.failed == 0
        assert result.duration_seconds >= 0
        assert result.errors == []
        assert job.status == "completed"

    def test_execute_batch_with_failures(self):
        processor = BatchProcessor()

        def fail_on_odd(record):
            if record["value"] % 2 != 0:
                raise ValueError(f"odd value: {record['value']}")
            return record["value"] * 2

        processor.process_fn = fail_on_odd
        job = processor.create_batch(
            name="fail-job",
            records=[{"value": i} for i in range(6)],
            config={"chunk_size": 2},
        )
        result = processor.execute_batch(job)
        assert result.processed == 3
        assert result.failed == 3
        assert len(result.errors) == 3


class TestEmptyBatch:
    """test_empty_batch: empty batch returns defaults."""

    def test_empty_batch(self):
        processor = BatchProcessor()
        job = processor.create_batch("empty-job", [], {})
        result = processor.execute_batch(job)
        assert isinstance(result, BatchResult)
        assert result.processed == 0
        assert result.failed == 0
        assert result.duration_seconds >= 0
        assert result.errors == []

    def test_empty_batch_report(self):
        processor = BatchProcessor()
        job = processor.create_batch("empty-report", [], {})
        result = processor.execute_batch(job)
        report = processor.generate_batch_report(result)
        assert report["total"] == 0
        assert report["success_rate"] == 0.0


class TestBatchValidation:
    """test_batch_validation: batch validated."""

    def test_validate_batch_valid(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="valid-job",
            records=[{"id": 1}],
            config={},
        )
        assert processor.validate_batch(job) is True

    def test_validate_batch_invalid_empty_name(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="",
            records=[{"id": 1}],
            config={},
        )
        assert processor.validate_batch(job) is False

    def test_validate_batch_invalid_no_records(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="no-records",
            records=[],
            config={},
        )
        assert processor.validate_batch(job) is False

    def test_validate_batch_invalid_bad_config(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="bad-config",
            records=[{"id": 1}],
            config={"chunk_size": -1},
        )
        assert processor.validate_batch(job) is False


class TestBatchReport:
    """test_batch_report: report generated."""

    def test_generate_batch_report(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="report-job",
            records=[{"id": i} for i in range(8)],
            config={"chunk_size": 4},
        )
        result = processor.execute_batch(job)
        report = processor.generate_batch_report(result)
        assert isinstance(report, dict)
        assert report["job_id"] == job.job_id
        assert report["job_name"] == "report-job"
        assert report["total"] == 8
        assert report["processed"] == 8
        assert report["failed"] == 0
        assert report["success_rate"] == 1.0
        assert report["duration_seconds"] >= 0

    def test_generate_batch_report_with_errors(self):
        processor = BatchProcessor()

        def fail_on_odd(record):
            if record["value"] % 2 != 0:
                raise ValueError("odd")
            return record

        processor.process_fn = fail_on_odd
        job = processor.create_batch(
            name="error-report",
            records=[{"value": i} for i in range(4)],
            config={},
        )
        result = processor.execute_batch(job)
        report = processor.generate_batch_report(result)
        assert report["total"] == 4
        assert report["processed"] == 2
        assert report["failed"] == 2
        assert report["success_rate"] == 0.5
        assert len(report["errors"]) == 2


class TestBatchErrorHandling:
    """test_batch_error_handling: errors handled."""

    def test_handle_batch_errors(self):
        processor = BatchProcessor()
        errors = [ValueError("err1"), TypeError("err2"), RuntimeError("err3")]
        handled = processor.handle_batch_errors(errors)
        assert isinstance(handled, list)
        assert len(handled) == 3
        assert all(isinstance(e, str) for e in handled)
        assert "err1" in handled[0]
        assert "err2" in handled[1]
        assert "err3" in handled[2]

    def test_handle_batch_errors_empty(self):
        processor = BatchProcessor()
        handled = processor.handle_batch_errors([])
        assert handled == []

    def test_handle_batch_errors_preserves_type_info(self):
        processor = BatchProcessor()
        errors = [ValueError("bad value")]
        handled = processor.handle_batch_errors(errors)
        assert "ValueError" in handled[0]
        assert "bad value" in handled[0]


class TestBatchMonitoring:
    """test_batch_monitoring: batch monitored."""

    def test_monitor_batch(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="monitor-job",
            records=[{"id": i} for i in range(5)],
            config={"chunk_size": 2},
        )
        status = processor.monitor_batch(job)
        assert isinstance(status, dict)
        assert status["job_id"] == job.job_id
        assert status["job_name"] == "monitor-job"
        assert status["status"] == "pending"
        assert status["total_records"] == 5
        assert status["progress"] == 0.0

    def test_monitor_batch_after_execution(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="monitor-exec",
            records=[{"id": i} for i in range(4)],
            config={},
        )
        processor.execute_batch(job)
        status = processor.monitor_batch(job)
        assert status["status"] == "completed"
        assert status["progress"] == 1.0


class TestBatchOptimization:
    """test_batch_optimization: batch optimized."""

    def test_optimize_batch(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="optimize-job",
            records=[{"id": i} for i in range(100)],
            config={"chunk_size": 10, "parallel": False},
        )
        optimized = processor.optimize_batch(job)
        assert isinstance(optimized, BatchJob)
        assert optimized.job_id == job.job_id
        assert optimized.name == job.name
        assert len(optimized.records) == len(job.records)
        # Optimization should adjust chunk_size based on record count
        assert "chunk_size" in optimized.config

    def test_optimize_batch_enables_parallel_for_large(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="large-optimize",
            records=[{"id": i} for i in range(1000)],
            config={"chunk_size": 10, "parallel": False},
        )
        optimized = processor.optimize_batch(job)
        # Large batches should benefit from parallel processing
        assert optimized.config.get("parallel") is True

    def test_optimize_batch_small_stays_sequential(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="small-optimize",
            records=[{"id": i} for i in range(3)],
            config={"chunk_size": 10, "parallel": False},
        )
        optimized = processor.optimize_batch(job)
        # Small batches should stay sequential
        assert optimized.config.get("parallel") is False


class TestBatchScheduling:
    """test_batch_scheduling: batch scheduled."""

    def test_schedule_batch(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="schedule-job",
            records=[{"id": 1}],
            config={},
        )
        schedule_id = processor.schedule_batch(job, "daily")
        assert isinstance(schedule_id, str)
        assert len(schedule_id) > 0
        assert job.status == "scheduled"

    def test_schedule_batch_with_cron(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="cron-job",
            records=[{"id": 1}],
            config={},
        )
        schedule_id = processor.schedule_batch(job, "0 2 * * *")
        assert isinstance(schedule_id, str)
        assert job.status == "scheduled"

    def test_schedule_batch_invalid_schedule(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="bad-schedule",
            records=[{"id": 1}],
            config={},
        )
        with pytest.raises(ValueError):
            processor.schedule_batch(job, "")


class TestBatchRetry:
    """test_batch_retry: retry logic works."""

    def test_retry_batch_success(self):
        processor = BatchProcessor()
        job = processor.create_batch(
            name="retry-job",
            records=[{"id": i} for i in range(3)],
            config={},
        )
        result = processor.retry_batch(job, max_retries=3)
        assert isinstance(result, BatchResult)
        assert result.processed == 3
        assert result.failed == 0

    def test_retry_batch_eventually_succeeds(self):
        processor = BatchProcessor()
        call_count = 0

        def flaky_process(record):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("transient error")
            return record

        processor.process_fn = flaky_process
        job = processor.create_batch(
            name="flaky-job",
            records=[{"id": 1}],
            config={},
        )
        result = processor.retry_batch(job, max_retries=5)
        assert result.processed == 1
        assert result.failed == 0

    def test_retry_batch_exhausts_retries(self):
        processor = BatchProcessor()

        def always_fail(record):
            raise RuntimeError("permanent error")

        processor.process_fn = always_fail
        job = processor.create_batch(
            name="doomed-job",
            records=[{"id": 1}],
            config={},
        )
        result = processor.retry_batch(job, max_retries=2)
        assert result.processed == 0
        assert result.failed == 1
        assert len(result.errors) > 0

    def test_retry_batch_zero_retries(self):
        processor = BatchProcessor()

        def always_fail(record):
            raise RuntimeError("error")

        processor.process_fn = always_fail
        job = processor.create_batch(
            name="zero-retry",
            records=[{"id": 1}],
            config={},
        )
        result = processor.retry_batch(job, max_retries=0)
        assert result.failed == 1
