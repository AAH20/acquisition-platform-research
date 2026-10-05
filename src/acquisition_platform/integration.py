"""Integration module for the acquisition platform.

Provides a lightweight framework for managing data integrations between
external systems (CRMs, data warehouses, APIs) and the platform.

Key components:
- Integration: dataclass representing a configured integration.
- SyncResult: dataclass capturing the outcome of a data sync.
- IntegrationManager: orchestrates creation, sync, validation, monitoring,
  error handling, optimization, security checks, scaling, and reporting.
"""
from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Integration:
    """A configured data integration.

    Attributes:
        integration_id: Unique identifier for the integration.
        name: Human-readable name.
        source: Source system identifier (e.g. "salesforce").
        target: Target system identifier (e.g. "data-warehouse").
        status: Current status ("active", "paused", "error").
        config: Arbitrary configuration dictionary.
    """

    integration_id: str
    name: str
    source: str
    target: str
    status: str
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncResult:
    """Outcome of a data synchronization run.

    Attributes:
        integration: The integration that was synced.
        records_synced: Number of records successfully synchronized.
        errors: Number of errors encountered during sync.
        duration_seconds: Wall-clock duration of the sync operation.
    """

    integration: Integration
    records_synced: int
    errors: int
    duration_seconds: float


class IntegrationManager:
    """Manages the lifecycle of data integrations.

    Provides methods for creating, syncing, validating, monitoring,
    error-handling, optimizing, securing, scaling, and reporting on
    integrations. State is kept in-memory; no external dependencies.
    """

    def __init__(self) -> None:
        self._integrations: dict[str, Integration] = {}
        self._sync_history: dict[str, list[SyncResult]] = {}

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def create_integration(
        self,
        name: str,
        source: str,
        target: str,
        config: dict[str, Any] | None = None,
    ) -> Integration:
        """Create and register a new integration.

        Args:
            name: Human-readable integration name.
            source: Source system identifier.
            target: Target system identifier.
            config: Optional configuration dictionary.

        Returns:
            The newly created Integration instance.
        """
        integration = Integration(
            integration_id=str(uuid.uuid4()),
            name=name,
            source=source,
            target=target,
            status="active",
            config=dict(config) if config else {},
        )
        self._integrations[integration.integration_id] = integration
        self._sync_history[integration.integration_id] = []
        return integration

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    def sync_data(self, integration: Integration) -> SyncResult:
        """Synchronize data for the given integration.

        Simulates a sync run. Empty source/target integrations sync zero
        records. Otherwise a deterministic record count is derived from the
        integration configuration.

        Args:
            integration: The integration to synchronize.

        Returns:
            SyncResult with records synced, errors, and duration.
        """
        start = time.perf_counter()

        if not integration.source or not integration.target:
            # Empty integration: nothing to sync
            result = SyncResult(
                integration=integration,
                records_synced=0,
                errors=0,
                duration_seconds=time.perf_counter() - start,
            )
        else:
            batch_size = int(integration.config.get("batch_size", 100))
            # Deterministic record count based on integration id
            seed = int(hashlib.md5(integration.integration_id.encode()).hexdigest(), 16)
            records = (seed % 1000) + batch_size
            errors = seed % 5
            result = SyncResult(
                integration=integration,
                records_synced=records,
                errors=errors,
                duration_seconds=time.perf_counter() - start,
            )

        self._sync_history.setdefault(integration.integration_id, []).append(result)
        return result

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_integration(self, integration: Integration) -> bool:
        """Validate an integration's configuration.

        An integration is valid if it has a non-empty name, source, and
        target, and its status is a recognized value.

        Args:
            integration: The integration to validate.

        Returns:
            True if the integration is valid, False otherwise.
        """
        if not integration.name:
            return False
        if not integration.source or not integration.target:
            return False
        if integration.status not in ("active", "paused", "error"):
            return False
        return True

    # ------------------------------------------------------------------
    # Monitoring
    # ------------------------------------------------------------------

    def monitor_integration(self, integration: Integration) -> dict[str, Any]:
        """Return monitoring metrics for an integration.

        Args:
            integration: The integration to monitor.

        Returns:
            Dictionary with status, uptime, last sync, and history count.
        """
        history = self._sync_history.get(integration.integration_id, [])
        last_sync = history[-1] if history else None
        return {
            "integration_id": integration.integration_id,
            "status": integration.status,
            "uptime_seconds": 0.0 if last_sync is None else last_sync.duration_seconds,
            "last_sync": last_sync is not None,
            "total_syncs": len(history),
            "total_records_synced": sum(r.records_synced for r in history),
            "total_errors": sum(r.errors for r in history),
        }

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def handle_integration_errors(self, errors: list[str]) -> list[str]:
        """Process a list of integration error messages.

        Returns a list of human-readable, actionable error descriptions.
        Each error is prefixed with a severity tag based on keywords.

        Args:
            errors: Raw error message strings.

        Returns:
            List of processed error description strings.
        """
        handled: list[str] = []
        for error in errors:
            lower = error.lower()
            if "timeout" in lower or "connection" in lower:
                handled.append(f"[RETRY] {error}")
            elif "schema" in lower or "mismatch" in lower:
                handled.append(f"[SCHEMA] {error}")
            elif "rate" in lower or "limit" in lower:
                handled.append(f"[BACKOFF] {error}")
            elif "auth" in lower or "credential" in lower:
                handled.append(f"[AUTH] {error}")
            else:
                handled.append(f"[ERROR] {error}")
        return handled

    # ------------------------------------------------------------------
    # Optimization
    # ------------------------------------------------------------------

    def optimize_integration(self, integration: Integration) -> Integration:
        """Return an optimized copy of the given integration.

        Doubles the batch size and enables compression in the config.
        The original integration is not modified.

        Args:
            integration: The integration to optimize.

        Returns:
            A new Integration with optimized configuration.
        """
        new_config = dict(integration.config)
        current_batch = int(new_config.get("batch_size", 10))
        new_config["batch_size"] = current_batch * 2
        new_config["compression"] = True
        new_config["optimized"] = True
        return Integration(
            integration_id=integration.integration_id,
            name=integration.name,
            source=integration.source,
            target=integration.target,
            status=integration.status,
            config=new_config,
        )

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    def check_integration_security(self, integration: Integration) -> bool:
        """Check whether an integration meets security requirements.

        Requires encryption to be configured and the integration to have
        a valid (non-empty) source and target.

        Args:
            integration: The integration to check.

        Returns:
            True if the integration passes security checks.
        """
        if not integration.source or not integration.target:
            return False
        encryption = integration.config.get("encryption")
        if not encryption:
            return False
        # Accept any non-empty encryption value
        return bool(encryption)

    # ------------------------------------------------------------------
    # Scaling
    # ------------------------------------------------------------------

    def scale_integration(self, integration: Integration, factor: int) -> Integration:
        """Return a scaled copy of the given integration.

        Multiplies the worker count by the given factor. The original
        integration is not modified.

        Args:
            integration: The integration to scale.
            factor: Multiplier for the worker count.

        Returns:
            A new Integration with scaled configuration.
        """
        new_config = dict(integration.config)
        current_workers = int(new_config.get("workers", 1))
        new_config["workers"] = current_workers * factor
        new_config["scaled"] = True
        return Integration(
            integration_id=integration.integration_id,
            name=integration.name,
            source=integration.source,
            target=integration.target,
            status=integration.status,
            config=new_config,
        )

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def generate_integration_report(self, result: SyncResult) -> dict[str, Any]:
        """Generate a report from a sync result.

        Args:
            result: The SyncResult to report on.

        Returns:
            Dictionary with integration details and sync metrics.
        """
        return {
            "integration_id": result.integration.integration_id,
            "name": result.integration.name,
            "source": result.integration.source,
            "target": result.integration.target,
            "status": result.integration.status,
            "records_synced": result.records_synced,
            "errors": result.errors,
            "duration_seconds": result.duration_seconds,
            "success_rate": (
                result.records_synced / (result.records_synced + result.errors)
                if (result.records_synced + result.errors) > 0
                else 0.0
            ),
        }
