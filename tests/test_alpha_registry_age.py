"""Tests for evidence ageing: a production alpha must expire.

Falsifiable predictions:
- A gate with ``max_age_days`` refuses promotion once the card is older than
  the limit, and says why.
- Without ``max_age_days`` the age check is inert (backwards compatibility).
- Age is computed from the card timestamp, never negative.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from acquisition_platform.alpha_registry import EvaluationCard, PromotionGate
from acquisition_platform.exceptions import InvalidRangeError

NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)


def make_card(age_days: float) -> EvaluationCard:
    created = NOW - timedelta(days=age_days)
    return EvaluationCard(
        alpha_id="alpha-age",
        params={"gap_weight": 0.34},
        metrics={"ndcg@5": 0.95, "delta": 0.20, "generalization_gap": 0.01},
        ci_low=0.10,
        ci_high=0.30,
        p_value=0.001,
        dataset_fingerprint="fp",
        code_version="0.2.0",
        seed=7,
        created_at=created.isoformat(),
    )


class TestGateAge:
    def test_fresh_evidence_passes(self):
        gate = PromotionGate(max_age_days=30)
        assert gate.failures(make_card(2), now=NOW) == []

    def test_stale_evidence_is_refused(self):
        gate = PromotionGate(max_age_days=30)
        reasons = gate.failures(make_card(45), now=NOW)
        assert len(reasons) == 1
        assert "stale" in reasons[0]
        assert "45.0 days" in reasons[0]

    def test_age_limit_is_inert_when_unset(self):
        gate = PromotionGate()
        assert gate.failures(make_card(400), now=NOW) == []

    def test_age_boundary_is_inclusive(self):
        gate = PromotionGate(max_age_days=30)
        assert gate.failures(make_card(30), now=NOW) == []
        assert gate.failures(make_card(30.5), now=NOW) != []

    def test_rejects_non_positive_limit(self):
        with pytest.raises(InvalidRangeError):
            PromotionGate(max_age_days=0)


class TestRegistryAge:
    def test_age_days_matches_timestamp(self, tmp_path):
        from acquisition_platform.alpha_registry import AlphaRegistry

        registry = AlphaRegistry(tmp_path / "registry.json")
        registry.register(make_card(12.5))
        assert registry.age_days("alpha-age", now=NOW) == pytest.approx(12.5, abs=1e-6)

    def test_is_stale(self, tmp_path):
        from acquisition_platform.alpha_registry import AlphaRegistry

        registry = AlphaRegistry(tmp_path / "registry.json")
        registry.register(make_card(12.5))
        assert registry.is_stale("alpha-age", 7, now=NOW) is True
        assert registry.is_stale("alpha-age", 30, now=NOW) is False

    def test_promotion_blocked_by_stale_evidence(self, tmp_path):
        from acquisition_platform.alpha_registry import AlphaRegistry

        registry = AlphaRegistry(tmp_path / "registry.json")
        registry.register(make_card(45))
        decision = registry.promote(
            "alpha-age", PromotionGate(max_age_days=30), now=NOW
        )
        assert decision.promoted is False
        assert registry.stage_of("alpha-age") == "shadow"

    def test_promotion_allowed_for_fresh_evidence(self, tmp_path):
        from acquisition_platform.alpha_registry import AlphaRegistry

        registry = AlphaRegistry(tmp_path / "registry.json")
        registry.register(make_card(1))
        decision = registry.promote(
            "alpha-age", PromotionGate(max_age_days=30), now=NOW
        )
        assert decision.promoted is True
        assert decision.stage == "canary"

    def test_rejects_non_positive_limit(self, tmp_path):
        from acquisition_platform.alpha_registry import AlphaRegistry

        registry = AlphaRegistry(tmp_path / "registry.json")
        registry.register(make_card(1))
        with pytest.raises(InvalidRangeError):
            registry.is_stale("alpha-age", 0, now=NOW)
