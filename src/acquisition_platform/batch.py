"""Batch processing module for chunked and parallel execution.

Provides utilities for processing large collections in manageable chunks,
with optional parallel execution via thread pools.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar, cast

from acquisition_platform.exceptions import ValidationError

T = TypeVar("T")
R = TypeVar("R")


@dataclass
class BatchConfig:
    """Configuration for batch processing.

    Attributes:
        chunk_size: Number of items to process in each chunk.
        max_workers: Maximum number of worker threads for parallel processing.
        parallel: Whether to process chunks in parallel.
    """

    chunk_size: int = 100
    max_workers: int = 4
    parallel: bool = False

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValidationError(f"chunk_size must be positive, got {self.chunk_size}")
        if self.max_workers <= 0:
            raise ValidationError(f"max_workers must be positive, got {self.max_workers}")


@dataclass
class BatchResult:
    """Result of a batch processing operation.

    Attributes:
        results: Successfully processed results in order.
        errors: List of (index, exception) tuples for failed items.
        processing_time: Wall-clock time in seconds.
    """

    results: list[Any] = field(default_factory=list)
    errors: list[tuple[int, Exception]] = field(default_factory=list)
    processing_time: float = 0.0


def _chunk(items: list[T], chunk_size: int) -> list[list[T]]:
    """Split a list into chunks of at most chunk_size elements."""
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def process_in_batches(
    items: list[T],
    processor_fn: Callable[[T], R],
    config: BatchConfig,
) -> list[R]:
    """Process items in chunks sequentially.

    Args:
        items: List of items to process.
        processor_fn: Function to apply to each item.
        config: Batch configuration.

    Returns:
        List of results in the same order as input items.
    """
    if not items:
        return []

    chunks = _chunk(items, config.chunk_size)
    results: list[R] = []

    for chunk in chunks:
        for item in chunk:
            results.append(processor_fn(item))

    return results


def process_in_parallel(
    items: list[T],
    processor_fn: Callable[[T], R],
    max_workers: int,
) -> list[R]:
    """Process items in parallel using a thread pool.

    Args:
        items: List of items to process.
        processor_fn: Function to apply to each item.
        max_workers: Maximum number of worker threads.

    Returns:
        List of results in the same order as input items.
    """
    if not items:
        return []
    if max_workers <= 0:
        raise ValidationError(f"max_workers must be positive, got {max_workers}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(processor_fn, items))


class BatchProcessor:
    """Processes items in batches with optional parallel execution.

    Attributes:
        config: BatchConfig instance controlling chunk size and parallelism.
    """

    def __init__(self, config: BatchConfig | None = None) -> None:
        self.config = config or BatchConfig()

    def process(
        self,
        items: list[T],
        processor_fn: Callable[[T], R],
    ) -> BatchResult:
        """Process items in batches, collecting results and errors.

        Args:
            items: List of items to process.
            processor_fn: Function to apply to each item.

        Returns:
            BatchResult with results, errors, and processing time.
        """
        start = time.monotonic()
        results: list[R] = []
        errors: list[tuple[int, Exception]] = []

        if not items:
            return BatchResult(results=[], errors=[], processing_time=0.0)

        chunks = _chunk(items, self.config.chunk_size)

        if self.config.parallel:
            # Process chunks in parallel using thread pool
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                # Submit all chunks and collect with original indices
                futures = {}
                global_idx = 0
                for chunk in chunks:
                    for item in chunk:
                        future = executor.submit(self._safe_process, item, processor_fn)
                        futures[future] = global_idx
                        global_idx += 1

                for future, idx in futures.items():
                    result, error = future.result()
                    if error is not None:
                        errors.append((idx, error))
                    else:
                        # When error is None, result is guaranteed to be non-None
                        results.append(cast(R, result))
        else:
            # Sequential processing
            global_idx = 0
            for chunk in chunks:
                for item in chunk:
                    result, error = self._safe_process(item, processor_fn)
                    if error is not None:
                        errors.append((global_idx, error))
                    elif result is not None:
                        results.append(result)
                    global_idx += 1

        elapsed = time.monotonic() - start
        return BatchResult(results=results, errors=errors, processing_time=elapsed)

    @staticmethod
    def _safe_process(
        item: T,
        processor_fn: Callable[[T], R],
    ) -> tuple[R | None, Exception | None]:
        """Process a single item, catching exceptions."""
        try:
            return processor_fn(item), None
        except Exception as e:
            return None, e
