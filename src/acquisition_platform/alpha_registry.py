"""Append-only alpha registry with promotion gates.

Every state change is an event in a hash-chained log: registering an alpha,
promoting it between stages, or rolling it back. Because each record commits to
the previous one, editing history after the fact is detectable — the property
an audit needs and a mutable "current status" table cannot provide.

Stage machine::

    shadow -> canary -> production
       \\         \\           \\
        +---------+-----------+--> rolled_back

Promotion is refused unless every gate passes, and the refusal names each
failed gate so the decision is reviewable.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from acquisition_platform.exceptions import InvalidRangeError, ValidationError

STAGES: tuple[str, ...] = ("shadow", "canary", "production", "rolled_back")
_PROMOTION_PATH: dict[str, str] = {"shadow": "canary", "canary": "production"}


def _canonical(payload: dict[str, Any]) -> str:
    """Serialise a payload deterministically for hashing."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


@dataclass(frozen=True)
class EvaluationCard:
    """Immutable record of how an alpha was produced and measured."""

    alpha_id: str
    params: dict[str, float]
    metrics: dict[str, float]
    ci_low: float
    ci_high: float
    p_value: float
    dataset_fingerprint: str
    code_version: str
    seed: int
    created_at: str

    def __post_init__(self) -> None:
        if not self.alpha_id:
            raise ValidationError("alpha_id cannot be empty")
        if not 0.0 <= self.p_value <= 1.0:
            raise InvalidRangeError(f"p_value must be in [0, 1], got {self.p_value}")
        if self.ci_low > self.ci_high:
            raise InvalidRangeError("ci_low cannot exceed ci_high")

    def digest(self) -> str:
        """Stable content hash of the card."""
        return hashlib.sha256(_canonical(self.to_dict()).encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {
            "alpha_id": self.alpha_id,
            "params": dict(self.params),
            "metrics": dict(self.metrics),
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "p_value": self.p_value,
            "dataset_fingerprint": self.dataset_fingerprint,
            "code_version": self.code_version,
            "seed": self.seed,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvaluationCard":
        """Rebuild a card from its dictionary form."""
        return cls(
            alpha_id=str(payload["alpha_id"]),
            params={key: float(value) for key, value in payload["params"].items()},
            metrics={key: float(value) for key, value in payload["metrics"].items()},
            ci_low=float(payload["ci_low"]),
            ci_high=float(payload["ci_high"]),
            p_value=float(payload["p_value"]),
            dataset_fingerprint=str(payload["dataset_fingerprint"]),
            code_version=str(payload["code_version"]),
            seed=int(payload["seed"]),
            created_at=str(payload["created_at"]),
        )

    @classmethod
    def create(
        cls,
        alpha_id: str,
        params: dict[str, float],
        metrics: dict[str, float],
        ci_low: float,
        ci_high: float,
        p_value: float,
        dataset_fingerprint: str,
        code_version: str,
        seed: int,
    ) -> "EvaluationCard":
        """Build a card stamped with the current UTC time."""
        return cls(
            alpha_id=alpha_id,
            params=params,
            metrics=metrics,
            ci_low=ci_low,
            ci_high=ci_high,
            p_value=p_value,
            dataset_fingerprint=dataset_fingerprint,
            code_version=code_version,
            seed=seed,
            created_at=datetime.now(timezone.utc).isoformat(),
        )


@dataclass(frozen=True)
class PromotionGate:
    """Thresholds an alpha must clear to advance a stage."""

    min_ndcg: float = 0.90
    min_delta: float = 0.05
    max_p_value: float = 0.05
    max_generalization_gap: float = 0.10

    def failures(self, card: EvaluationCard) -> list[str]:
        """Return one human-readable reason per failed gate."""
        reasons: list[str] = []
        ndcg = float(card.metrics.get("ndcg@5", 0.0))
        delta = float(card.metrics.get("delta", 0.0))
        gap = float(card.metrics.get("generalization_gap", 0.0))
        if ndcg < self.min_ndcg:
            reasons.append(f"ndcg {ndcg:.4f} below minimum {self.min_ndcg:.4f}")
        if delta < self.min_delta:
            reasons.append(f"delta {delta:.4f} below minimum {self.min_delta:.4f}")
        if card.p_value > self.max_p_value:
            reasons.append(
                f"p_value {card.p_value:.4f} above maximum {self.max_p_value:.4f}"
            )
        if gap > self.max_generalization_gap:
            reasons.append(
                f"generalization gap {gap:.4f} above maximum "
                f"{self.max_generalization_gap:.4f}"
            )
        return reasons


@dataclass(frozen=True)
class PromotionDecision:
    """Outcome of a promotion attempt."""

    promoted: bool
    stage: str
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {
            "promoted": self.promoted,
            "stage": self.stage,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class RegistryEvent:
    """One immutable record in the registry's hash chain."""

    sequence: int
    event_type: str
    alpha_id: str
    stage: str
    card: EvaluationCard | None
    prev_hash: str
    record_hash: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {
            "sequence": self.sequence,
            "event_type": self.event_type,
            "alpha_id": self.alpha_id,
            "stage": self.stage,
            "card": self.card.to_dict() if self.card is not None else None,
            "prev_hash": self.prev_hash,
            "record_hash": self.record_hash,
            "note": self.note,
        }

    def compute_hash(self) -> str:
        """Recompute this record's hash from its committed fields."""
        return hashlib.sha256(
            _canonical(
                {
                    "sequence": self.sequence,
                    "event_type": self.event_type,
                    "alpha_id": self.alpha_id,
                    "stage": self.stage,
                    "card": self.card.to_dict() if self.card is not None else None,
                    "prev_hash": self.prev_hash,
                    "note": self.note,
                }
            ).encode()
        ).hexdigest()


class AlphaRegistry:
    """Persistent, tamper-evident registry of evaluated alphas."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._events: list[RegistryEvent] = []
        self._load()

    # -- persistence -------------------------------------------------------

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        events: list[RegistryEvent] = []
        for item in payload.get("events", []):
            card_payload = item.get("card")
            events.append(
                RegistryEvent(
                    sequence=int(item["sequence"]),
                    event_type=str(item["event_type"]),
                    alpha_id=str(item["alpha_id"]),
                    stage=str(item["stage"]),
                    card=EvaluationCard.from_dict(card_payload) if card_payload else None,
                    prev_hash=str(item["prev_hash"]),
                    record_hash=str(item["record_hash"]),
                    note=str(item.get("note", "")),
                )
            )
        self._events = events

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "events": [event.to_dict() for event in self._events],
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # -- log ---------------------------------------------------------------

    @property
    def events(self) -> list[RegistryEvent]:
        """All events in append order."""
        return list(self._events)

    def _append(
        self,
        event_type: str,
        alpha_id: str,
        stage: str,
        card: EvaluationCard | None = None,
        note: str = "",
    ) -> RegistryEvent:
        sequence = len(self._events)
        prev_hash = self._events[-1].record_hash if self._events else ""
        event = RegistryEvent(
            sequence=sequence,
            event_type=event_type,
            alpha_id=alpha_id,
            stage=stage,
            card=card,
            prev_hash=prev_hash,
            record_hash="",
            note=note,
        )
        event = RegistryEvent(
            sequence=event.sequence,
            event_type=event.event_type,
            alpha_id=event.alpha_id,
            stage=event.stage,
            card=event.card,
            prev_hash=event.prev_hash,
            record_hash=event.compute_hash(),
            note=event.note,
        )
        self._events.append(event)
        self._save()
        return event

    def verify(self) -> bool:
        """Return True when every hash and link is intact."""
        previous = ""
        for index, event in enumerate(self._events):
            if event.sequence != index:
                return False
            if event.prev_hash != previous:
                return False
            if event.record_hash != event.compute_hash():
                return False
            previous = event.record_hash
        return True

    # -- queries -----------------------------------------------------------

    def _events_for(self, alpha_id: str) -> list[RegistryEvent]:
        return [event for event in self._events if event.alpha_id == alpha_id]

    def get(self, alpha_id: str) -> EvaluationCard:
        """Return the registered card for an alpha."""
        for event in self._events_for(alpha_id):
            if event.event_type == "register" and event.card is not None:
                return event.card
        raise ValidationError(f"alpha '{alpha_id}' is not registered")

    def stage_of(self, alpha_id: str) -> str:
        """Return the current stage of an alpha."""
        history = self._events_for(alpha_id)
        if not history:
            raise ValidationError(f"alpha '{alpha_id}' is not registered")
        return history[-1].stage

    def latest(self, stage: str | None = None) -> EvaluationCard | None:
        """Return the most recently registered card, optionally filtered by stage."""
        candidates: list[tuple[int, EvaluationCard]] = []
        seen: set[str] = set()
        for event in self._events:
            if event.event_type != "register" or event.card is None:
                continue
            if event.alpha_id in seen:
                continue
            seen.add(event.alpha_id)
            if stage is None or self.stage_of(event.alpha_id) == stage:
                candidates.append((event.sequence, event.card))
        if not candidates:
            return None
        return max(candidates, key=lambda pair: pair[0])[1]

    # -- mutations ---------------------------------------------------------

    def register(self, card: EvaluationCard, stage: str = "shadow") -> str:
        """Append a registration event for a new alpha."""
        if stage not in STAGES:
            raise ValidationError(f"unknown stage '{stage}'")
        if self._events_for(card.alpha_id):
            raise ValidationError(f"alpha '{card.alpha_id}' is already registered")
        self._append("register", card.alpha_id, stage, card=card)
        return card.alpha_id

    def promote(
        self, alpha_id: str, gate: PromotionGate | None = None
    ) -> PromotionDecision:
        """Attempt to advance an alpha to the next stage."""
        active_gate = gate or PromotionGate()
        card = self.get(alpha_id)
        stage = self.stage_of(alpha_id)

        if stage == "production":
            return PromotionDecision(
                promoted=False,
                stage=stage,
                reasons=("alpha is already in production",),
            )
        if stage == "rolled_back":
            return PromotionDecision(
                promoted=False,
                stage=stage,
                reasons=("alpha has been rolled back and cannot be promoted",),
            )

        failures = active_gate.failures(card)
        if failures:
            return PromotionDecision(
                promoted=False, stage=stage, reasons=tuple(failures)
            )

        next_stage = _PROMOTION_PATH[stage]
        self._append("promote", alpha_id, next_stage)
        return PromotionDecision(promoted=True, stage=next_stage)

    def rollback(self, alpha_id: str, reason: str = "") -> str:
        """Retire an alpha and record why."""
        self.get(alpha_id)
        self._append("rollback", alpha_id, "rolled_back", note=reason)
        return "rolled_back"
