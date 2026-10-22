"""Tests for the append-only alpha registry and promotion gates.

Acceptance gates:
- The event log is hash-chained and tamper-evident.
- Promotion is impossible when any gate fails, and the reason is named.
- Stage transitions follow shadow -> canary -> production; rollback is durable.
"""

from __future__ import annotations

import json

import pytest

from acquisition_platform.alpha_registry import (
    AlphaRegistry,
    EvaluationCard,
    PromotionGate,
)
from acquisition_platform.exceptions import ValidationError


def card(alpha_id: str = "alpha-1", **overrides) -> EvaluationCard:
    metrics = {
        "ndcg@5": 0.95,
        "delta": 0.20,
        "generalization_gap": 0.01,
    }
    metrics.update(overrides.pop("metrics", {}))
    payload = {
        "alpha_id": alpha_id,
        "params": {"gap_weight": 0.34, "midpoint_weight": 0.53},
        "metrics": metrics,
        "ci_low": 0.15,
        "ci_high": 0.25,
        "p_value": 0.001,
        "dataset_fingerprint": "e7423ecd",
        "code_version": "0.2.0",
        "seed": 7,
        "created_at": "2026-10-22T00:00:00+00:00",
    }
    payload.update(overrides)
    return EvaluationCard(**payload)


@pytest.fixture()
def registry(tmp_path) -> AlphaRegistry:
    return AlphaRegistry(tmp_path / "registry.json")


class TestRegistration:
    def test_register_and_get(self, registry):
        registry.register(card())
        stored = registry.get("alpha-1")
        assert stored.alpha_id == "alpha-1"
        assert stored.metrics["ndcg@5"] == 0.95

    def test_duplicate_registration_rejected(self, registry):
        registry.register(card())
        with pytest.raises(ValidationError):
            registry.register(card())

    def test_unknown_alpha_raises(self, registry):
        with pytest.raises(ValidationError):
            registry.get("missing")

    def test_new_alpha_starts_in_shadow(self, registry):
        registry.register(card())
        assert registry.stage_of("alpha-1") == "shadow"

    def test_persists_across_instances(self, tmp_path):
        path = tmp_path / "registry.json"
        AlphaRegistry(path).register(card())
        reopened = AlphaRegistry(path)
        assert reopened.get("alpha-1").alpha_id == "alpha-1"
        assert reopened.verify() is True


class TestPromotion:
    def test_promotion_moves_shadow_to_canary(self, registry):
        registry.register(card())
        decision = registry.promote("alpha-1", PromotionGate())
        assert decision.promoted is True
        assert decision.stage == "canary"
        assert registry.stage_of("alpha-1") == "canary"

    def test_second_promotion_moves_to_production(self, registry):
        registry.register(card())
        registry.promote("alpha-1", PromotionGate())
        decision = registry.promote("alpha-1", PromotionGate())
        assert decision.promoted is True
        assert decision.stage == "production"

    def test_low_ndcg_blocks_promotion(self, registry):
        registry.register(card(metrics={"ndcg@5": 0.50}))
        decision = registry.promote("alpha-1", PromotionGate(min_ndcg=0.90))
        assert decision.promoted is False
        assert any("ndcg" in reason for reason in decision.reasons)
        assert registry.stage_of("alpha-1") == "shadow"

    def test_insignificant_result_blocks_promotion(self, registry):
        registry.register(card(p_value=0.40))
        decision = registry.promote("alpha-1", PromotionGate(max_p_value=0.05))
        assert decision.promoted is False
        assert any("p_value" in reason for reason in decision.reasons)

    def test_large_generalisation_gap_blocks_promotion(self, registry):
        registry.register(card(metrics={"generalization_gap": 0.40}))
        decision = registry.promote("alpha-1", PromotionGate(max_generalization_gap=0.10))
        assert decision.promoted is False
        assert any("gap" in reason for reason in decision.reasons)

    def test_small_delta_blocks_promotion(self, registry):
        registry.register(card(metrics={"delta": 0.01}))
        decision = registry.promote("alpha-1", PromotionGate(min_delta=0.05))
        assert decision.promoted is False
        assert any("delta" in reason for reason in decision.reasons)

    def test_production_promotion_is_terminal(self, registry):
        registry.register(card())
        registry.promote("alpha-1", PromotionGate())
        registry.promote("alpha-1", PromotionGate())
        decision = registry.promote("alpha-1", PromotionGate())
        assert decision.promoted is False
        assert any("production" in reason for reason in decision.reasons)


class TestRollbackAndAudit:
    def test_rollback_changes_stage(self, registry):
        registry.register(card())
        registry.rollback("alpha-1", reason="canary regression")
        assert registry.stage_of("alpha-1") == "rolled_back"

    def test_rolled_back_alpha_cannot_be_promoted(self, registry):
        registry.register(card())
        registry.rollback("alpha-1", reason="incident")
        decision = registry.promote("alpha-1", PromotionGate())
        assert decision.promoted is False

    def test_event_log_is_append_only(self, registry):
        registry.register(card())
        registry.promote("alpha-1", PromotionGate())
        types = [event.event_type for event in registry.events]
        assert types == ["register", "promote"]
        assert registry.events[0].sequence == 0
        assert registry.events[1].sequence == 1

    def test_chain_is_linked(self, registry):
        registry.register(card())
        registry.promote("alpha-1", PromotionGate())
        assert registry.events[0].prev_hash == ""
        assert registry.events[1].prev_hash == registry.events[0].record_hash

    def test_verify_passes_on_intact_log(self, registry):
        registry.register(card())
        registry.promote("alpha-1", PromotionGate())
        assert registry.verify() is True

    def test_verify_detects_tampering(self, tmp_path):
        path = tmp_path / "registry.json"
        registry = AlphaRegistry(path)
        registry.register(card())
        payload = json.loads(path.read_text())
        payload["events"][0]["card"]["metrics"]["ndcg@5"] = 0.01
        path.write_text(json.dumps(payload))
        reopened = AlphaRegistry(path)
        assert reopened.verify() is False

    def test_card_digest_is_stable(self):
        assert card().digest() == card().digest()

    def test_card_digest_changes_with_metrics(self):
        assert card().digest() != card(metrics={"ndcg@5": 0.10}).digest()

    def test_latest_returns_most_recent_for_stage(self, registry):
        registry.register(card("alpha-1"))
        registry.register(card("alpha-2"))
        registry.promote("alpha-2", PromotionGate())
        assert registry.latest(stage="canary").alpha_id == "alpha-2"
        assert registry.latest(stage="shadow").alpha_id == "alpha-1"
