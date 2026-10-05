"""Batch processing module for job-based batch operations.

Provides a higher-level batch processing abstraction with job tracking,
validation, monitoring, optimization, scheduling, and retry logic.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class BatchJob:
    """Represents a batch processing job.

    Attributes:
        job_id: Unique identifier for the job.
        name: Human-readable name for the job.
        status: Current status (pending, running, completed, failed, scheduled).
        records: List of record dict[str, Any]s to process.
        config: Configuration dict[str, Any] for the job.
    """

    job_id: str
    name: str
    status: str
    records: list[dict[str, Any]]
    config: dict[str, Any]


@dataclass
class BatchResult:
    """Result of a batch job execution.

    Attributes:
        job: The BatchJob that was executed.
        processed: Number of records successfully processed.
        failed: Number of records that failed.
        duration_seconds: Wall-clock execution time.
        errors: List of error message strings.
    """

    job: BatchJob
    processed: int
    failed: int
    duration_seconds: float
    errors: list[str]


class BatchProcessor:
    """Processes batch jobs with monitoring, optimization, and retry support.

    Attributes:
        process_fn: Optional callable to process each record.
    """

    def __init__(self, process_fn: Callable[[dict[str, Any]], Any] | None = None) -> None:
        self.process_fn = process_fn or self._default_process_fn

    @staticmethod
    def _default_process_fn(record: dict[str, Any]) -> dict[str, Any]:
        """Default processing function that returns the record unchanged."""
        return record

    def create_batch(
        self,
        name: str,
        records: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> BatchJob:
        """Create a new batch job.

        Args:
            name: Human-readable name for the batch.
            records: List of record dict[str, Any]s to process.
            config: Optional configuration dict[str, Any].

        Returns:
            A new BatchJob with status 'pending'.
        """
        return BatchJob(
            job_id=str(uuid.uuid4()),
            name=name,
            status="pending",
            records=list(records),
            config=dict[str, Any](config) if config else {},
        )

    def execute_batch(self, job: BatchJob) -> BatchResult:
        """Execute a batch job.

        Args:
            job: The BatchJob to execute.

        Returns:
            BatchResult with processing statistics.
        """
        job.status = "running"
        start = time.monotonic()
        processed = 0
        failed = 0
        errors: list[str] = []

        for record in job.records:
            try:
                self.process_fn(record)
                processed += 1
            except Exception as e:
                failed += 1
                errors.append(f"{type(e).__name__}: {e}")

        elapsed = time.monotonic() - start
        job.status = "completed" if failed == 0 else "failed"

        return BatchResult(
            job=job,
            processed=processed,
            failed=failed,
            duration_seconds=elapsed,
            errors=errors,
        )

    def validate_batch(self, job: BatchJob) -> bool:
        """Validate a batch job before execution.

        Args:
            job: The BatchJob to validate.

        Returns:
            True if the job is valid, False otherwise.
        """
        if not job.name or not job.name.strip():
            return False
        if not job.records:
            return False
        chunk_size = job.config.get("chunk_size")
        if chunk_size is not None and chunk_size <= 0:
            return False
        return True

    def handle_batch_errors(self, errors: list[Exception]) -> list[str]:
        """Convert a list of exceptions to formatted error strings.

        Args:
            errors: List of exception objects.

        Returns:
            List of formatted error message strings.
        """
        return [f"{type(e).__name__}: {e}" for e in errors]

    def monitor_batch(self, job: BatchJob) -> dict[str, Any]:
        """Get monitoring status for a batch job.

        Args:
            job: The BatchJob to monitor.

        Returns:
            Dict with job status information.
        """
        total = len(job.records)
        if job.status == "completed":
            progress = 1.0
        elif job.status == "failed":
            progress = 1.0
        elif job.status == "running":
            progress = 0.5
        else:
            progress = 0.0

        return {
            "job_id": job.job_id,
            "job_name": job.name,
            "status": job.status,
            "total_records": total,
            "progress": progress,
        }

    def optimize_batch(self, job: BatchJob) -> BatchJob:
        """Optimize batch configuration based on record count.

        For large batches (>100 records), enables parallel processing
        and adjusts chunk size for better throughput.

        Args:
            job: The BatchJob to optimize.

        Returns:
            The same BatchJob with optimized config.
        """
        record_count = len(job.records)
        if record_count > 100:
            job.config["parallel"] = True
            job.config["chunk_size"] = min(50, max(10, record_count // 10))
        else:
            job.config["parallel"] = False
            job.config["chunk_size"] = min(10, max(1, record_count))
        return job

    def schedule_batch(self, job: BatchJob, schedule: str) -> str:
        """Schedule a batch job for future execution.

        Args:
            job: The BatchJob to schedule.
            schedule: Schedule expression (e.g., 'daily', 'hourly', cron string).

        Returns:
            A schedule ID string.

        Raises:
            ValueError: If schedule is empty or invalid.
        """
        if not schedule or not schedule.strip():
            raise ValueError("Schedule expression cannot be empty")

        job.status = "scheduled"
        return f"sched-{uuid.uuid4().hex[:12]}"

    def retry_batch(self, job: BatchJob, max_retries: int) -> BatchResult:
        """Execute a batch job with retry logic.

        Retries the entire batch up to max_retries times if it fails.

        Args:
            job: The BatchJob to execute.
            max_retries: Maximum number of retry attempts.

        Returns:
            BatchResult from the final attempt.
        """
        result = self.execute_batch(job)

        for _ in range(max_retries):
            if result.failed == 0:
                break
            result = self.execute_batch(job)

        return result

    def generate_batch_report(self, result: BatchResult) -> dict[str, Any]:
        """Generate a report from a batch result.

        Args:
            result: The BatchResult to report on.

        Returns:
            Dict with report data.
        """
        total = result.processed + result.failed
        success_rate = result.processed / total if total > 0 else 0.0

        return {
            "job_id": result.job.job_id,
            "job_name": result.job.name,
            "total": total,
            "processed": result.processed,
            "failed": result.failed,
            "success_rate": success_rate,
            "duration_seconds": result.duration_seconds,
            "errors": result.errors,
        }
