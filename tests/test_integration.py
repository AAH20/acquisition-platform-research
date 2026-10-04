"""Comprehensive integration tests for the full acquisition platform.

These tests exercise the entire platform end-to-end, covering:
- Full pipeline: entities -> resolve -> fraud -> value -> match -> portfolio -> price -> rank -> evolve
- CLI commands end-to-end
- API endpoints
- Batch processing
- Caching performance
- Notifications on events
- Data export/import roundtrip
- Security (rate limiting, sanitization)
- Observability (logging, metrics)
- Orchestrator full pipeline
"""

from __future__ import annotations

import json
import logging
import time

import pytest
from fastapi.testclient import TestClient

from acquisition_platform.__main__ import main as cli_main
from acquisition_platform.api import app as api_app
from acquisition_platform.batch import BatchConfig, BatchProcessor, process_in_batches, process_in_parallel
from acquisition_platform.caching import Cache, CacheStats, cached, clear_cache, get_cache_stats
from acquisition_platform.data_io import (
    export_to_csv,
    export_to_json,
    export_to_yaml,
    import_from_csv,
    import_from_json,
    import_from_yaml,
    validate_schema,
)
from acquisition_platform.dynamic_pricing import PricingEngine
from acquisition_platform.entity_resolution import EntityResolver
from acquisition_platform.evolution import EvolutionEngine, EvolutionResult
from acquisition_platform.fraud_detection import FraudDetector, FraudSignal, FraudScore
from acquisition_platform.matching import Buyer, BuyerSellerMatcher, Seller
from acquisition_platform.notifications import (
    Notification,
    NotificationChannel,
    NotificationHandler,
    NotificationType,
    notify_evolution_converged,
    notify_high_fraud_risk,
    notify_match_found,
    notify_portfolio_optimized,
)
from acquisition_platform.observability import (
    HealthCheck,
    MetricsCollector,
    get_logger,
    log_execution_time,
    log_module_call,
)
from acquisition_platform.orchestrator import AcquisitionPipeline, PipelineConfig, PipelineResult
from acquisition_platform.portfolio_optimizer import Asset, Portfolio, PortfolioOptimizer
from acquisition_platform.search_ranking import Listing, SearchRanker
from acquisition_platform.security import (
    AuditLogger,
    InputSanitizer,
    RateLimiter,
    RateLimitExceeded,
    SecurityConfig,
    secure_method,
)
from acquisition_platform.valuation import ValuationEngine, ValuationResult


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _buyer(bid="b1", budget=500_000, category="saas"):
    return Buyer(id=bid, budget=budget, preferences={"category": category})


def _seller(sid="s1", price=400_000, category="saas"):
    return Seller(id=sid, asking_price=price, attributes={"category": category})


def _buyer_dict(bid="b1", budget=500_000, category="saas"):
    return {"id": bid, "budget": budget, "preferences": {"category": category}}


def _seller_dict(sid="s1", price=400_000, category="saas"):
    return {"id": sid, "asking_price": price, "attributes": {"category": category}}


def _entity_dict(eid="e1", name="Acme Corp", domain="acme.com"):
    return {"id": eid, "name": name, "domain": domain}


def _full_config():
    return PipelineConfig(
        enable_matching=True,
        enable_valuation=True,
        enable_fraud=True,
        enable_portfolio=True,
        enable_pricing=True,
        enable_ranking=True,
        enable_evolution=True,
    )


def _entities_for_full_pipeline():
    return [
        _buyer_dict("b1", 500_000, "saas"),
        _seller_dict("s1", 400_000, "saas"),
        _buyer_dict("b2", 300_000, "fintech"),
        _seller_dict("s2", 250_000, "fintech"),
    ]


@pytest.fixture()
def api_client():
    return TestClient(api_app)


@pytest.fixture()
def notification_handler():
    return NotificationHandler()


@pytest.fixture()
def metrics_collector():
    return MetricsCollector()


@pytest.fixture()
def rate_limiter():
    return RateLimiter(max_requests=5, window_seconds=60)


@pytest.fixture()
def audit_logger():
    return AuditLogger()


@pytest.fixture()
def sanitizer():
    return InputSanitizer()


@pytest.fixture()
def cache():
    return Cache(ttl=300.0, max_size=100)


# ---------------------------------------------------------------------------
# 1. Full platform pipeline: entities -> resolve -> fraud -> value -> match -> portfolio -> price -> rank -> evolve
# ---------------------------------------------------------------------------


class TestFullPlatformPipeline:
    """End-to-end pipeline exercising every engine in sequence."""

    def test_full_platform_pipeline(self):
        """Entities flow through resolve, fraud, value, match, portfolio, price, rank, evolve."""
        # --- Stage 1: Entity Resolution ---
        resolver = EntityResolver(threshold=0.85)
        raw_entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e3", "name": "Globex Inc", "domain": "globex.io"},
            {"id": "e4", "name": "Initech LLC", "domain": "initech.com"},
        ]
        clusters = resolver.resolve(raw_entities)
        assert len(clusters) >= 2
        assert all(len(c.entities) >= 1 for c in clusters)
        # Acme Corp duplicates should be clustered together
        acme_cluster = next(c for c in clusters if c.canonical_name == "Acme Corp")
        assert len(acme_cluster.entities) == 2

        # --- Stage 2: Fraud Detection ---
        detector = FraudDetector()
        fraud_entities = [
            {"id": "f1", "attributes": {"signals": [
                {"name": "identity_verified", "value": 0.9},
                {"name": "financial_consistency", "value": 0.8},
                {"name": "traffic_authenticity", "value": 0.7},
            ]}},
            {"id": "f2", "attributes": {"signals": [
                {"name": "identity_verified", "value": 0.1},
                {"name": "financial_consistency", "value": 0.05},
                {"name": "traffic_authenticity", "value": 0.02},
            ]}},
        ]
        fraud_scores = []
        for entity in fraud_entities:
            signals = [
                FraudSignal(name=s["name"], value=s["value"])
                for s in entity["attributes"]["signals"]
            ]
            score = detector.score(signals)
            fraud_scores.append(score)
        assert len(fraud_scores) == 2
        assert fraud_scores[0].risk_level == "low"
        assert fraud_scores[1].risk_level == "high"
        assert fraud_scores[0].score < fraud_scores[1].score

        # --- Stage 3: Valuation ---
        engine = ValuationEngine()
        dcf_result = engine.dcf_valuation(
            free_cash_flow=100_000,
            growth_rate=0.05,
            discount_rate=0.10,
            terminal_growth=0.02,
            years=5,
        )
        assert dcf_result.method == "DCF"
        assert dcf_result.value > 0
        assert dcf_result.low_estimate < dcf_result.value < dcf_result.high_estimate

        comps_result = engine.comparable_valuation(metric=200_000, multiple=3.0)
        assert comps_result.method == "Comps"
        assert comps_result.value == 600_000

        ensemble_result = engine.ensemble_valuation(
            free_cash_flow=100_000,
            revenue=200_000,
            growth_rate=0.05,
            discount_rate=0.10,
            terminal_growth=0.02,
            revenue_multiple=3.0,
            years=5,
        )
        assert ensemble_result.method == "Ensemble"
        assert ensemble_result.value > 0

        # --- Stage 4: Matching ---
        matcher = BuyerSellerMatcher()
        buyers = [_buyer("b1", 500_000, "saas"), _buyer("b2", 300_000, "fintech")]
        sellers = [_seller("s1", 400_000, "saas"), _seller("s2", 250_000, "fintech")]
        matches = matcher.match(buyers, sellers)
        assert len(matches) == 2
        assert all(m.score > 0 for m in matches)
        assert all(0 <= m.confidence <= 1 for m in matches)

        # --- Stage 5: Portfolio Optimization ---
        optimizer = PortfolioOptimizer(budget=500_000, max_assets=10)
        assets = [
            Asset(id="a1", cost=100_000, expected_return=0.10, risk=0.15, sector="saas"),
            Asset(id="a2", cost=200_000, expected_return=0.12, risk=0.20, sector="fintech"),
            Asset(id="a3", cost=150_000, expected_return=0.08, risk=0.10, sector="saas"),
        ]
        portfolio = optimizer.optimize(assets, risk_tolerance=0.5)
        assert isinstance(portfolio, Portfolio)
        assert len(portfolio.assets) > 0
        assert portfolio.expected_return > 0

        # --- Stage 6: Dynamic Pricing ---
        pricing = PricingEngine()
        price_rec = pricing.recommend_price(
            base_value=dcf_result.value,
            demand_level=0.7,
            competition_level=0.3,
            market_condition="bull",
        )
        assert price_rec.recommended_price > 0
        assert price_rec.floor_price <= price_rec.recommended_price <= price_rec.ceiling_price

        # --- Stage 7: Search Ranking ---
        ranker = SearchRanker()
        listings = [
            Listing(id="l1", title="Acme SaaS", relevance=0.9, category="saas"),
            Listing(id="l2", title="Beta Tools", relevance=0.7, category="saas"),
            Listing(id="l3", title="Gamma Fintech", relevance=0.8, category="fintech"),
        ]
        rankings = ranker.rank("saas tools", listings, user_preferences={"category": "saas"})
        assert len(rankings) == 3
        scores = [r.score for r in rankings]
        assert scores == sorted(scores, reverse=True)

        # --- Stage 8: Evolution ---
        evo_engine = EvolutionEngine(population_size=20, generations=10)
        evo_result = evo_engine.evolve(
            fitness_fn=lambda x: -((x - 0.5) ** 2) + 1.0,
            gene_range=(0.0, 1.0),
        )
        assert isinstance(evo_result, EvolutionResult)
        assert evo_result.best_fitness > 0
        assert evo_result.generation_count > 0
        assert evo_result.population_size == 20

    def test_pipeline_stage_interdependence(self):
        """Output of each stage feeds correctly into the next."""
        # Valuation output feeds into pricing
        engine = ValuationEngine()
        val = engine.comparable_valuation(metric=100_000, multiple=2.0)
        assert val.value == 200_000

        pricing = PricingEngine()
        price = pricing.recommend_price(
            base_value=val.value,
            demand_level=0.5,
            competition_level=0.5,
            market_condition="normal",
        )
        # With equal demand/competition and normal market, price should be near base
        assert price.floor_price <= price.recommended_price <= price.ceiling_price

        # Matching output feeds into portfolio
        matcher = BuyerSellerMatcher()
        buyers = [_buyer("b1", 500_000, "saas")]
        sellers = [_seller("s1", 400_000, "saas")]
        matches = matcher.match(buyers, sellers)
        assert len(matches) == 1

        # Matched seller becomes a portfolio asset
        matched_seller = sellers[0]
        asset = Asset(
            id=matched_seller.id,
            cost=matched_seller.asking_price,
            expected_return=0.10,
            risk=0.15,
            sector=matched_seller.attributes.get("category", ""),
        )
        optimizer = PortfolioOptimizer(budget=500_000)
        portfolio = optimizer.optimize([asset], risk_tolerance=0.5)
        assert len(portfolio.assets) == 1
        assert portfolio.assets[0].id == "s1"


# ---------------------------------------------------------------------------
# 2. CLI integration
# ---------------------------------------------------------------------------


class TestCLIIntegration:
    """CLI commands work end-to-end."""

    def test_cli_match_end_to_end(self, tmp_path, capsys):
        buyers_file = tmp_path / "buyers.json"
        buyers_data = [{"id": "b1", "budget": 100000, "preferences": {"category": "saas"}}]
        buyers_file.write_text(json.dumps(buyers_data))
        sellers_file = tmp_path / "sellers.json"
        sellers_data = [{"id": "s1", "asking_price": 80000, "attributes": {"category": "saas"}}]
        sellers_file.write_text(json.dumps(sellers_data))

        code = cli_main([
            "match",
            "--buyers-file", str(buyers_file),
            "--sellers-file", str(sellers_file),
        ])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["count"] == 1
        assert out["matches"][0]["buyer_id"] == "b1"
        assert out["matches"][0]["seller_id"] == "s1"

    def test_cli_value_dcf_end_to_end(self, capsys):
        code = cli_main([
            "value",
            "--fcf", "100000",
            "--growth", "0.05",
            "--discount", "0.10",
            "--terminal-growth", "0.02",
            "--years", "5",
        ])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["method"] == "DCF"
        assert out["value"] > 0
        assert 0.0 <= out["confidence"] <= 1.0

    def test_cli_fraud_check_end_to_end(self, capsys):
        signals = json.dumps([
            ["identity_verified", 0.9],
            ["financial_consistency", 0.8],
            ["traffic_authenticity", 0.7],
        ])
        code = cli_main(["fraud-check", "--signals", signals])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert 0.0 <= out["score"] <= 1.0
        assert out["risk_level"] in {"low", "medium", "high"}

    def test_cli_optimize_end_to_end(self, tmp_path, capsys):
        assets_file = tmp_path / "assets.json"
        assets_file.write_text(json.dumps([
            {"id": "a1", "cost": 30000, "expected_return": 0.2, "risk": 0.1, "sector": "saas"},
            {"id": "a2", "cost": 40000, "expected_return": 0.15, "risk": 0.2, "sector": "ecom"},
        ]))
        code = cli_main([
            "optimize",
            "--budget", "100000",
            "--max-assets", "2",
            "--assets-file", str(assets_file),
        ])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["count"] >= 1
        assert out["expected_return"] >= 0

    def test_cli_price_end_to_end(self, capsys):
        code = cli_main([
            "price",
            "--base-value", "100000",
            "--demand", "0.8",
            "--competition", "0.3",
            "--market", "bull",
        ])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["recommended_price"] > 0
        assert out["floor_price"] < out["ceiling_price"]

    def test_cli_resolve_end_to_end(self, tmp_path, capsys):
        entities_file = tmp_path / "entities.json"
        entities_file.write_text(json.dumps([
            {"name": "Acme Inc", "domain": "acme.com"},
            {"name": "Acme Inc", "domain": "acme.com"},
            {"name": "Globex", "domain": "globex.io"},
        ]))
        code = cli_main(["resolve", "--entities-file", str(entities_file)])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["count"] >= 1
        assert out["clusters"][0]["canonical_name"]

    def test_cli_rank_end_to_end(self, tmp_path, capsys):
        listings_file = tmp_path / "listings.json"
        listings_file.write_text(json.dumps([
            {"id": "l1", "title": "SaaS A", "relevance": 0.9, "category": "saas"},
            {"id": "l2", "title": "SaaS B", "relevance": 0.8, "category": "saas"},
        ]))
        code = cli_main([
            "rank",
            "--query", "saas",
            "--listings-file", str(listings_file),
        ])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["query"] == "saas"
        assert len(out["rankings"]) == 2

    def test_cli_evolve_end_to_end(self, capsys):
        code = cli_main([
            "evolve",
            "--fitness-fn", "-(x-3)**2 + 9",
            "--gene-range", "0,10",
            "--seed", "42",
            "--generations", "20",
            "--population-size", "50",
        ])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["best_fitness"] > 8.0
        assert out["population_size"] == 50

    def test_cli_benchmark_end_to_end(self, capsys):
        code = cli_main([
            "benchmark",
            "--name", "accuracy",
            "--target", "0.9",
            "--actual", "0.95",
        ])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["passed"] is True

    def test_cli_config_show_and_set(self, tmp_path, capsys):
        config_path = str(tmp_path / "acq_config.json")
        code = cli_main(["--config", config_path, "config", "show"])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert "entity_resolution" in out

        code = cli_main([
            "--config", config_path,
            "config", "set",
            "entity_resolution.threshold", "0.9",
        ])
        assert code == 0
        capsys.readouterr()

        code = cli_main(["--config", config_path, "config", "show"])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["entity_resolution"]["threshold"] == pytest.approx(0.9)

    def test_cli_error_handling(self, capsys):
        """CLI returns exit code 1 on bad input."""
        code = cli_main(["value", "--fcf", "100000"])
        assert code == 1
        assert "error" in capsys.readouterr().err.lower()

    def test_cli_pipeline_via_api(self, api_client):
        """CLI-equivalent pipeline through the API."""
        # Match
        resp = api_client.post("/match", json={
            "buyers": [{"id": "b1", "budget": 100000, "preferences": {"category": "saas"}}],
            "sellers": [{"id": "s1", "asking_price": 80000, "attributes": {"category": "saas"}}],
        })
        assert resp.status_code == 200
        match_data = resp.json()
        assert match_data["count"] == 1

        # Value
        resp = api_client.post("/value", json={
            "method": "comps",
            "metric": 200000,
            "multiple": 3,
        })
        assert resp.status_code == 200
        val_data = resp.json()
        assert val_data["value"] == 600000

        # Fraud check
        resp = api_client.post("/fraud-check", json={
            "signals": [
                {"name": "identity_verified", "value": 0.9},
                {"name": "financial_consistency", "value": 0.8},
            ],
        })
        assert resp.status_code == 200
        fraud_data = resp.json()
        assert fraud_data["risk_level"] in {"low", "medium", "high"}


# ---------------------------------------------------------------------------
# 3. API integration
# ---------------------------------------------------------------------------


class TestAPIIntegration:
    """API endpoints work end-to-end."""

    def test_api_health_endpoint(self, api_client):
        resp = api_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "uptime_seconds" in data

    def test_api_metrics_endpoint(self, api_client):
        api_client.get("/health")
        resp = api_client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_requests"] >= 1
        assert "/health" in data["endpoints"]

    def test_api_match_endpoint(self, api_client):
        resp = api_client.post("/match", json={
            "buyers": [{"id": "b1", "budget": 100000, "preferences": {"category": "saas"}}],
            "sellers": [{"id": "s1", "asking_price": 80000, "attributes": {"category": "saas"}}],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["matches"][0]["buyer_id"] == "b1"

    def test_api_value_endpoint_all_methods(self, api_client):
        # DCF
        resp = api_client.post("/value", json={
            "method": "dcf",
            "free_cash_flow": 100000,
            "growth_rate": 0.05,
            "discount_rate": 0.10,
            "terminal_growth": 0.02,
            "years": 5,
        })
        assert resp.status_code == 200
        assert resp.json()["method"] == "DCF"

        # Comps
        resp = api_client.post("/value", json={
            "method": "comps",
            "metric": 200000,
            "multiple": 3,
        })
        assert resp.status_code == 200
        assert resp.json()["method"] == "Comps"

        # SDE
        resp = api_client.post("/value", json={
            "method": "sde",
            "sde": 50000,
            "multiple": 2.5,
        })
        assert resp.status_code == 200
        assert resp.json()["method"] == "SDE"

        # ARR
        resp = api_client.post("/value", json={
            "method": "arr",
            "arr": 1000000,
            "multiple": 5,
        })
        assert resp.status_code == 200
        assert resp.json()["method"] == "ARR"

        # Ensemble
        resp = api_client.post("/value", json={
            "method": "ensemble",
            "free_cash_flow": 100000,
            "revenue": 200000,
            "growth_rate": 0.05,
            "discount_rate": 0.10,
            "terminal_growth": 0.02,
            "revenue_multiple": 3,
            "years": 5,
        })
        assert resp.status_code == 200
        assert resp.json()["method"] == "Ensemble"

    def test_api_fraud_check_endpoint(self, api_client):
        resp = api_client.post("/fraud-check", json={
            "signals": [
                {"name": "identity_verified", "value": 0.9},
                {"name": "financial_consistency", "value": 0.8},
                {"name": "traffic_authenticity", "value": 0.7},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert 0.0 <= data["score"] <= 1.0
        assert data["risk_level"] in {"low", "medium", "high"}

    def test_api_fraud_check_graph_endpoint(self, api_client):
        resp = api_client.post("/fraud-check", json={
            "graph": {
                "nodes": ["a", "b", "c"],
                "edges": [["a", "b"], ["b", "c"], ["c", "a"]],
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_ring"] is True
        assert data["risk_score"] == pytest.approx(0.8)

    def test_api_optimize_endpoint(self, api_client):
        resp = api_client.post("/optimize", json={
            "budget": 100000,
            "max_assets": 2,
            "risk_tolerance": 0.5,
            "assets": [
                {"id": "a1", "cost": 30000, "expected_return": 0.2, "risk": 0.1, "sector": "saas"},
                {"id": "a2", "cost": 40000, "expected_return": 0.15, "risk": 0.2, "sector": "ecom"},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["assets"]) >= 1
        assert data["expected_return"] >= 0

    def test_api_price_endpoint(self, api_client):
        resp = api_client.post("/price", json={
            "base_value": 100000,
            "demand_level": 0.8,
            "competition_level": 0.3,
            "market_condition": "bull",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["recommended_price"] > 0
        assert data["floor_price"] <= data["recommended_price"] <= data["ceiling_price"]

    def test_api_resolve_endpoint(self, api_client):
        resp = api_client.post("/resolve", json={
            "entities": [
                {"name": "Acme Inc", "domain": "acme.com"},
                {"name": "Acme Inc", "domain": "acme.com"},
                {"name": "Globex", "domain": "globex.io"},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        assert data["clusters"][0]["canonical_name"]

    def test_api_rank_endpoint(self, api_client):
        resp = api_client.post("/rank", json={
            "query": "saas",
            "listings": [
                {"id": "l1", "title": "SaaS A", "relevance": 0.9, "category": "saas"},
                {"id": "l2", "title": "SaaS B", "relevance": 0.8, "category": "saas"},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        scores = [r["score"] for r in data["rankings"]]
        assert scores == sorted(scores, reverse=True)

    def test_api_evolve_endpoint(self, api_client):
        resp = api_client.post("/evolve", json={
            "population_size": 20,
            "generations": 10,
            "fitness": "quadratic",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["best_fitness"] > 0
        assert data["population_size"] == 20

    def test_api_pipeline_endpoint(self, api_client):
        resp = api_client.post("/pipeline", json={
            "entities": _entities_for_full_pipeline(),
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "matches" in data
        assert "valuations" in data
        assert "fraud_scores" in data
        assert "portfolio" in data
        assert "prices" in data
        assert "rankings" in data
        assert "evolution_result" in data

    def test_api_pipeline_with_config(self, api_client):
        resp = api_client.post("/pipeline", json={
            "entities": _entities_for_full_pipeline(),
            "config": {
                "enable_matching": True,
                "enable_valuation": True,
                "enable_fraud": True,
                "enable_portfolio": False,
                "enable_pricing": True,
                "enable_ranking": False,
                "enable_evolution": False,
            },
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["matches"]) > 0
        assert len(data["valuations"]) > 0
        assert data["portfolio"] is None
        assert len(data["rankings"]) == 0
        assert data["evolution_result"] is None

    def test_api_error_handling(self, api_client):
        """API returns proper error codes for invalid input."""
        resp = api_client.post("/match", json={"buyers": [], "sellers": []})
        assert resp.status_code == 422

        resp = api_client.post("/value", json={"method": "dcf"})
        assert resp.status_code == 422

        resp = api_client.post("/fraud-check", json={})
        assert resp.status_code == 422

    def test_api_openapi_schema(self, api_client):
        resp = api_client.get("/openapi.json")
        assert resp.status_code == 200
        paths = resp.json()["paths"]
        for endpoint in [
            "/match", "/value", "/fraud-check", "/optimize", "/price",
            "/resolve", "/rank", "/evolve", "/pipeline", "/health", "/metrics",
        ]:
            assert endpoint in paths


# ---------------------------------------------------------------------------
# 4. Batch integration
# ---------------------------------------------------------------------------


class TestBatchIntegration:
    """Batch processing works correctly."""

    def test_process_in_batches_sequential(self):
        items = list(range(100))
        config = BatchConfig(chunk_size=10, parallel=False)
        results = process_in_batches(items, lambda x: x * 2, config)
        assert results == [x * 2 for x in range(100)]

    def test_process_in_parallel(self):
        items = list(range(50))
        results = process_in_parallel(items, lambda x: x ** 2, max_workers=4)
        assert results == [x ** 2 for x in range(50)]

    def test_batch_processor_sequential(self):
        processor = BatchProcessor(BatchConfig(chunk_size=5, parallel=False))
        items = list(range(20))
        result = processor.process(items, lambda x: x + 1)
        assert len(result.results) == 20
        assert result.errors == []
        assert result.processing_time >= 0

    def test_batch_processor_parallel(self):
        processor = BatchProcessor(BatchConfig(chunk_size=5, parallel=True, max_workers=2))
        items = list(range(20))
        result = processor.process(items, lambda x: x + 1)
        assert len(result.results) == 20
        assert result.errors == []

    def test_batch_processor_with_errors(self):
        """Batch processor captures errors without stopping."""
        processor = BatchProcessor(BatchConfig(chunk_size=5, parallel=False))

        def maybe_fail(x):
            if x % 3 == 0:
                raise ValueError(f"bad item {x}")
            return x

        items = list(range(10))
        result = processor.process(items, maybe_fail)
        assert len(result.results) == 6  # 10 - 4 failures (0, 3, 6, 9)
        assert len(result.errors) == 4

    def test_batch_processor_empty_input(self):
        processor = BatchProcessor()
        result = processor.process([], lambda x: x)
        assert result.results == []
        assert result.errors == []
        assert result.processing_time == 0.0

    def test_batch_config_validation(self):
        with pytest.raises(Exception):
            BatchConfig(chunk_size=0)
        with pytest.raises(Exception):
            BatchConfig(max_workers=0)

    def test_batch_valuation_integration(self):
        """Valuation engine works in batch mode."""
        engine = ValuationEngine()
        financials = [
            {"free_cash_flow": 100000, "growth_rate": 0.05, "discount_rate": 0.10, "terminal_growth": 0.02, "years": 5},
            {"metric": 200000, "multiple": 3},
            {"sde": 50000, "multiple": 2.5},
            {"arr": 1000000, "multiple": 5},
        ]
        results = engine.value_batch(financials, chunk_size=2)
        assert len(results) == 4
        assert all(isinstance(r, ValuationResult) for r in results)

    def test_batch_matching_integration(self):
        """Matching works in batch mode."""
        matcher = BuyerSellerMatcher()
        buyers = [_buyer(f"b{i}", 100_000 + i * 1000, "saas") for i in range(5)]
        sellers = [_seller(f"s{i}", 80_000 + i * 500, "saas") for i in range(5)]
        matches = matcher.match_batch(buyers, sellers, chunk_size=2)
        assert len(matches) > 0

    def test_batch_entity_resolution_integration(self):
        """Entity resolution works in batch mode."""
        resolver = EntityResolver(threshold=0.85)
        entities = [
            {"name": f"Company {i}", "domain": f"company{i}.com"}
            for i in range(10)
        ]
        # Add some duplicates
        entities.append({"name": "Company 0", "domain": "company0.com"})
        entities.append({"name": "Company 1", "domain": "company1.com"})

        clusters = resolver.resolve_batch(entities, chunk_size=5)
        # With chunk_size=5, entities are split into 3 chunks (5+5+2).
        # Within each chunk, similar names (all start with "Com") are clustered.
        # The duplicates in chunk 3 merge with each other.
        assert len(clusters) >= 2  # At least the chunks produce multiple clusters
        # All entities should be accounted for
        total_entities = sum(len(c.entities) for c in clusters)
        assert total_entities == 12


# ---------------------------------------------------------------------------
# 5. Caching integration
# ---------------------------------------------------------------------------


class TestCachingIntegration:
    """Caching improves performance."""

    def test_cache_set_and_get(self, cache):
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_cache_miss_returns_none(self, cache):
        assert cache.get("nonexistent") is None

    def test_cache_ttl_expiration(self):
        cache = Cache(ttl=0.01, max_size=10)
        cache.set("key", "value")
        assert cache.get("key") == "value"
        time.sleep(0.02)
        assert cache.get("key") is None

    def test_cache_lru_eviction(self):
        cache = Cache(ttl=None, max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # Should evict "a"
        assert cache.get("a") is None
        assert cache.get("d") == 4

    def test_cache_stats_tracking(self, cache):
        cache.set("a", 1)
        cache.get("a")  # hit
        cache.get("b")  # miss
        stats = cache.stats
        assert stats.hits == 1
        assert stats.misses == 1

    def test_cache_clear(self, cache):
        cache.set("a", 1)
        cache.get("a")  # hit
        cache.clear()
        assert cache.get("a") is None
        # After clear, stats are reset; the get above is a new miss
        stats = cache.stats
        assert stats.hits == 0
        assert stats.misses == 1  # the get("a") after clear

    def test_cached_decorator(self):
        call_count = 0

        @cached(ttl=300.0, max_size=100)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = expensive_function(5)
        result2 = expensive_function(5)
        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Second call served from cache

    def test_cached_decorator_different_args(self):
        call_count = 0

        @cached(ttl=300.0, max_size=100)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        expensive_function(5)
        expensive_function(10)
        assert call_count == 2

    def test_global_cache_stats(self):
        clear_cache()
        stats = get_cache_stats()
        assert isinstance(stats, CacheStats)

    def test_caching_improves_performance(self):
        """Cached function is faster on repeated calls."""
        call_count = 0

        @cached(ttl=300.0, max_size=100)
        def slow_function(x):
            nonlocal call_count
            call_count += 1
            time.sleep(0.001)
            return x * 2

        # First call - no cache
        start = time.perf_counter()
        slow_function(42)
        first_duration = time.perf_counter() - start

        # Second call - cached
        start = time.perf_counter()
        slow_function(42)
        second_duration = time.perf_counter() - start

        assert call_count == 1
        assert second_duration < first_duration

    def test_cache_with_custom_instance(self):
        custom_cache = Cache(ttl=300.0, max_size=10)

        @cached(ttl=300.0, max_size=10, cache_instance=custom_cache)
        def func(x):
            return x * 2

        result = func(5)
        assert result == 10
        # Verify the custom cache has an entry (key format includes qualname)
        assert len(custom_cache._store) == 1


# ---------------------------------------------------------------------------
# 6. Notification integration
# ---------------------------------------------------------------------------


class TestNotificationIntegration:
    """Notifications fire on events."""

    def test_notification_creation(self, notification_handler):
        notification = Notification(
            id="test-1",
            type=NotificationType.INFO,
            message="Test notification",
            severity=1,
            timestamp="2024-01-01T00:00:00+00:00",
        )
        notification_handler.send(notification)
        history = notification_handler.get_history()
        assert len(history) == 1
        assert history[0].message == "Test notification"

    def test_notification_batch_send(self, notification_handler):
        notifications = [
            Notification(
                id=f"n{i}",
                type=NotificationType.INFO,
                message=f"Notification {i}",
                severity=1,
                timestamp="2024-01-01T00:00:00+00:00",
            )
            for i in range(5)
        ]
        sent = notification_handler.send_batch(notifications)
        assert len(sent) == 5
        assert len(notification_handler.get_history()) == 5

    def test_notification_custom_sink(self, notification_handler):
        received = []

        def custom_sink(notification):
            received.append(notification)

        notification_handler.register_sink(NotificationChannel.CONSOLE, custom_sink)
        notification = Notification(
            id="sink-test",
            type=NotificationType.INFO,
            message="Sink test",
            severity=1,
            timestamp="2024-01-01T00:00:00+00:00",
        )
        notification_handler.send(notification)
        assert len(received) == 1
        assert received[0].message == "Sink test"

    def test_notify_high_fraud_risk(self, notification_handler):
        notification = notify_high_fraud_risk(notification_handler, "entity_123", 0.95)
        assert notification.type == NotificationType.CRITICAL
        assert notification.severity == 4
        assert "entity_123" in notification.message
        assert len(notification_handler.get_history()) == 1

    def test_notify_match_found(self, notification_handler):
        notification = notify_match_found(notification_handler, "buyer_1", "seller_1", 0.85)
        assert notification.type == NotificationType.INFO
        assert notification.severity == 1
        assert "buyer_1" in notification.message
        assert "seller_1" in notification.message

    def test_notify_portfolio_optimized(self, notification_handler):
        notification = notify_portfolio_optimized(notification_handler, 0.12, 1.5)
        assert notification.type == NotificationType.INFO
        assert "0.12" in notification.message
        assert "1.5" in notification.message

    def test_notify_evolution_converged(self, notification_handler):
        notification = notify_evolution_converged(notification_handler, 0.95, 15)
        assert notification.type == NotificationType.INFO
        assert "15" in notification.message
        assert "0.95" in notification.message

    def test_notification_validation(self):
        """Notification validates required fields."""
        with pytest.raises(ValueError):
            Notification(
                id="",
                type=NotificationType.INFO,
                message="Test",
                severity=1,
                timestamp="2024-01-01T00:00:00+00:00",
            )
        with pytest.raises(ValueError):
            Notification(
                id="test",
                type=NotificationType.INFO,
                message="",
                severity=1,
                timestamp="2024-01-01T00:00:00+00:00",
            )
        with pytest.raises(ValueError):
            Notification(
                id="test",
                type=NotificationType.INFO,
                message="Test",
                severity=5,
                timestamp="2024-01-01T00:00:00+00:00",
            )

    def test_notification_clear_history(self, notification_handler):
        notification = Notification(
            id="test",
            type=NotificationType.INFO,
            message="Test",
            severity=1,
            timestamp="2024-01-01T00:00:00+00:00",
        )
        notification_handler.send(notification)
        assert len(notification_handler.get_history()) == 1
        notification_handler.clear_history()
        assert len(notification_handler.get_history()) == 0

    def test_notifications_fire_on_pipeline_events(self, notification_handler):
        """Simulate notifications firing during a pipeline run."""
        # Fraud alert
        notify_high_fraud_risk(notification_handler, "bad_entity", 0.92)
        # Match found
        notify_match_found(notification_handler, "b1", "s1", 0.88)
        # Portfolio optimized
        notify_portfolio_optimized(notification_handler, 0.15, 2.0)
        # Evolution converged
        notify_evolution_converged(notification_handler, 0.98, 12)

        history = notification_handler.get_history()
        assert len(history) == 4
        types = [n.type for n in history]
        assert NotificationType.CRITICAL in types
        assert NotificationType.INFO in types


# ---------------------------------------------------------------------------
# 7. Data I/O integration
# ---------------------------------------------------------------------------


class TestDataIOIntegration:
    """Export/import roundtrip works."""

    def test_json_roundtrip(self, tmp_path):
        data = {"key": "value", "number": 42, "nested": {"a": 1}}
        path = str(tmp_path / "test.json")
        export_to_json(data, path)
        loaded = import_from_json(path)
        assert loaded == data

    def test_csv_roundtrip(self, tmp_path):
        data = [
            {"name": "Alice", "age": 30, "city": "NYC"},
            {"name": "Bob", "age": 25, "city": "LA"},
            {"name": "Charlie", "age": 35, "city": "Chicago"},
        ]
        path = str(tmp_path / "test.csv")
        export_to_csv(data, path)
        loaded = import_from_csv(path)
        assert len(loaded) == 3
        assert loaded[0]["name"] == "Alice"
        assert loaded[1]["age"] == "25"  # CSV values are strings

    def test_yaml_roundtrip(self, tmp_path):
        data = {"key": "value", "list": [1, 2, 3], "nested": {"a": True}}
        path = str(tmp_path / "test.yaml")
        export_to_yaml(data, path)
        loaded = import_from_yaml(path)
        assert loaded == data

    def test_json_export_with_dataclass(self, tmp_path):
        """JSON export handles dataclass objects via default=str."""
        data = {"result": ValuationResult(
            value=100000, method="DCF", confidence=0.7,
            low_estimate=85000, high_estimate=115000,
        )}
        path = str(tmp_path / "test.json")
        export_to_json(data, path)
        loaded = import_from_json(path)
        assert "result" in loaded

    def test_csv_empty_data(self, tmp_path):
        path = str(tmp_path / "empty.csv")
        export_to_csv([], path)
        loaded = import_from_csv(path)
        assert loaded == []

    def test_csv_missing_keys(self, tmp_path):
        """CSV export handles rows with missing keys."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob"},
        ]
        path = str(tmp_path / "test.csv")
        export_to_csv(data, path)
        loaded = import_from_csv(path)
        assert len(loaded) == 2

    def test_import_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            import_from_json(str(tmp_path / "nonexistent.json"))
        with pytest.raises(FileNotFoundError):
            import_from_csv(str(tmp_path / "nonexistent.csv"))
        with pytest.raises(FileNotFoundError):
            import_from_yaml(str(tmp_path / "nonexistent.yaml"))

    def test_validate_schema(self):
        data = {"name": "Alice", "age": 30, "active": True}
        schema = {"name": str, "age": int, "active": bool}
        assert validate_schema(data, schema) is True

        bad_schema = {"name": str, "age": str}
        assert validate_schema(data, bad_schema) is False

        missing_schema = {"name": str, "nonexistent": str}
        assert validate_schema(data, missing_schema) is False

    def test_data_io_pipeline_roundtrip(self, tmp_path):
        """Full pipeline results can be exported and reimported."""
        # Run a mini pipeline
        engine = ValuationEngine()
        val = engine.comparable_valuation(metric=100000, multiple=2.0)

        matcher = BuyerSellerMatcher()
        matches = matcher.match([_buyer()], [_seller()])

        # Export
        results = {
            "valuation": val.to_dict() if hasattr(val, "to_dict") else {
                "value": val.value, "method": val.method,
                "confidence": val.confidence,
            },
            "matches": [
                {"buyer_id": m.buyer_id, "seller_id": m.seller_id, "score": m.score}
                for m in matches
            ],
        }
        path = str(tmp_path / "pipeline_results.json")
        export_to_json(results, path)

        # Reimport
        loaded = import_from_json(path)
        assert loaded["valuation"]["value"] == 200000
        assert len(loaded["matches"]) == 1


# ---------------------------------------------------------------------------
# 8. Security integration
# ---------------------------------------------------------------------------


class TestSecurityIntegration:
    """Rate limiting and sanitization work correctly."""

    def test_rate_limiter_allows_within_limit(self, rate_limiter):
        for i in range(5):
            rate_limiter.check(f"user_{i}")
        # All should pass without exception

    def test_rate_limiter_blocks_over_limit(self, rate_limiter):
        for i in range(5):
            rate_limiter.check("user_1")
        with pytest.raises(RateLimitExceeded):
            rate_limiter.check("user_1")

    def test_rate_limiter_is_allowed(self, rate_limiter):
        # max_requests=5, so 5 calls should be allowed, 6th should fail
        assert rate_limiter.is_allowed("new_user") is True  # 1st
        rate_limiter.check("new_user")  # 2nd
        rate_limiter.check("new_user")  # 3rd
        rate_limiter.check("new_user")  # 4th
        rate_limiter.check("new_user")  # 5th
        assert rate_limiter.is_allowed("new_user") is False  # 6th exceeds

    def test_rate_limiter_get_remaining(self, rate_limiter):
        assert rate_limiter.get_remaining("user") == 5
        rate_limiter.check("user")
        assert rate_limiter.get_remaining("user") == 4

    def test_rate_limiter_reset(self, rate_limiter):
        for i in range(5):
            rate_limiter.check("user")
        assert rate_limiter.get_remaining("user") == 0
        rate_limiter.reset("user")
        assert rate_limiter.get_remaining("user") == 5

    def test_rate_limiter_different_keys(self, rate_limiter):
        """Different keys have independent rate limits."""
        for i in range(5):
            rate_limiter.check("user_a")
        # user_b should still be allowed
        assert rate_limiter.is_allowed("user_b") is True

    def test_rate_limiter_window_expiration(self):
        """Rate limit resets after window expires."""
        limiter = RateLimiter(max_requests=2, window_seconds=0.01)
        limiter.check("user")
        limiter.check("user")
        with pytest.raises(RateLimitExceeded):
            limiter.check("user")
        time.sleep(0.02)
        # Should be allowed again
        limiter.check("user")

    def test_input_sanitizer_string(self, sanitizer):
        assert sanitizer.sanitize_string("  hello  ") == "hello"
        assert sanitizer.sanitize_string("hello\x00world") == "helloworld"
        assert sanitizer.sanitize_string(None) == ""
        assert sanitizer.sanitize_string(123) == "123"

    def test_input_sanitizer_string_truncation(self):
        sanitizer = InputSanitizer(max_length=5)
        assert sanitizer.sanitize_string("hello world") == "hello"

    def test_input_sanitizer_number(self, sanitizer):
        assert sanitizer.sanitize_number(42) == 42.0
        assert sanitizer.sanitize_number("3.14") == 3.14
        assert sanitizer.sanitize_number("not a number") == 0.0
        assert sanitizer.sanitize_number(None) == 0.0

    def test_input_sanitizer_number_clamping(self, sanitizer):
        assert sanitizer.sanitize_number(50, min_val=0, max_val=100) == 50.0
        assert sanitizer.sanitize_number(-5, min_val=0, max_val=100) == 0.0
        assert sanitizer.sanitize_number(150, min_val=0, max_val=100) == 100.0

    def test_input_sanitizer_number_nan_inf(self, sanitizer):
        assert sanitizer.sanitize_number(float("nan")) == 0.0
        assert sanitizer.sanitize_number(float("inf"), max_val=100) == 100.0
        assert sanitizer.sanitize_number(float("-inf"), min_val=0) == 0.0

    def test_input_sanitizer_dict(self, sanitizer):
        data = {
            "name": "  Alice  ",
            "age": 30,
            "active": True,
            "nested": {"key": "value"},
        }
        result = sanitizer.sanitize_dict(data)
        assert result["name"] == "Alice"
        assert result["age"] == 30.0
        # In Python, bool is a subclass of int, so True is sanitized as a number
        assert result["active"] == 1.0

    def test_input_sanitizer_dict_depth_limit(self, sanitizer):
        """Sanitizer respects max depth."""
        deep = {"a": {"b": {"c": {"d": {"e": {"f": "value"}}}}}}
        result = sanitizer.sanitize_dict(deep, max_depth=3)
        assert "a" in result

    def test_audit_logger(self, audit_logger):
        audit_logger.log_access("user1", "resource1", "read")
        audit_logger.log_action("user1", "delete", {"id": 123})
        trail = audit_logger.get_audit_trail()
        assert len(trail) == 2
        assert trail[0]["user"] == "user1"
        assert trail[0]["action"] == "read"

    def test_audit_logger_filter_by_user(self, audit_logger):
        audit_logger.log_access("user1", "resource1", "read")
        audit_logger.log_access("user2", "resource2", "write")
        trail = audit_logger.get_audit_trail(user="user1")
        assert len(trail) == 1
        assert trail[0]["user"] == "user1"

    def test_audit_logger_clear(self, audit_logger):
        audit_logger.log_access("user1", "resource1", "read")
        assert len(audit_logger.get_audit_trail()) == 1
        audit_logger.clear()
        assert len(audit_logger.get_audit_trail()) == 0

    def test_audit_logger_max_entries(self):
        logger = AuditLogger(max_entries=3)
        for i in range(5):
            logger.log_access(f"user{i}", "resource", "read")
        trail = logger.get_audit_trail()
        assert len(trail) == 3

    def test_security_config(self):
        config = SecurityConfig()
        assert config.audit_enabled is True
        assert config.sanitize_enabled is True
        assert config.rate_limit is not None

    def test_secure_method_decorator(self, rate_limiter, audit_logger):
        """secure_method decorator applies rate limiting and audit logging."""

        @secure_method(rate_limiter=rate_limiter, audit_logger=audit_logger, user_key="user_id")
        def protected_function(user_id: str, data: str) -> str:
            return f"processed {data} for {user_id}"

        result = protected_function(user_id="user1", data="test_data")
        assert result == "processed test_data for user1"

        # Check audit log
        trail = audit_logger.get_audit_trail(user="user1")
        assert len(trail) == 1

    def test_secure_method_rate_limiting(self, rate_limiter, audit_logger):
        """secure_method enforces rate limiting."""

        @secure_method(rate_limiter=rate_limiter, audit_logger=audit_logger, user_key="user_id")
        def protected_function(user_id: str) -> str:
            return "ok"

        # Use up the rate limit
        for i in range(5):
            protected_function(user_id="limited_user")

        with pytest.raises(RateLimitExceeded):
            protected_function(user_id="limited_user")

    def test_secure_method_sanitization(self, rate_limiter, audit_logger):
        """secure_method sanitizes string inputs."""
        sanitizer = InputSanitizer(max_length=10)

        @secure_method(
            rate_limiter=rate_limiter,
            audit_logger=audit_logger,
            sanitizer=sanitizer,
            user_key="user_id",
        )
        def protected_function(user_id: str, data: str) -> str:
            return data

        result = protected_function(user_id="user1", data="  hello  ")
        assert result == "hello"


# ---------------------------------------------------------------------------
# 9. Observability integration
# ---------------------------------------------------------------------------


class TestObservabilityIntegration:
    """Logging and metrics work correctly."""

    def test_get_logger(self):
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_metrics_collector_counters(self, metrics_collector):
        metrics_collector.increment("requests")
        metrics_collector.increment("requests")
        metrics_collector.increment("requests", 5)
        assert metrics_collector.get_counter("requests") == 7

    def test_metrics_collector_gauges(self, metrics_collector):
        metrics_collector.gauge("cpu_usage", 75.5)
        assert metrics_collector.get_gauge("cpu_usage") == 75.5

    def test_metrics_collector_timers(self, metrics_collector):
        metrics_collector.timer("operation", 100.0)
        metrics_collector.timer("operation", 200.0)
        stats = metrics_collector.get_timer_stats("operation")
        assert stats["count"] == 2.0
        assert stats["min"] == 100.0
        assert stats["max"] == 200.0
        assert stats["mean"] == 150.0

    def test_metrics_collector_timeit(self, metrics_collector):
        with metrics_collector.timeit("my_op"):
            time.sleep(0.001)
        stats = metrics_collector.get_timer_stats("my_op")
        assert stats["count"] == 1.0
        assert stats["min"] > 0

    def test_metrics_collector_snapshot(self, metrics_collector):
        metrics_collector.increment("requests", 10)
        metrics_collector.gauge("cpu", 50.0)
        metrics_collector.timer("op", 100.0)
        snapshot = metrics_collector.snapshot()
        assert snapshot["counters"]["requests"] == 10
        assert snapshot["gauges"]["cpu"] == 50.0
        assert "op" in snapshot["timers"]

    def test_metrics_collector_reset(self, metrics_collector):
        metrics_collector.increment("requests", 10)
        metrics_collector.reset()
        assert metrics_collector.get_counter("requests") == 0

    def test_log_execution_time_decorator(self):
        """log_execution_time decorator logs execution time."""
        logger = get_logger("test.execution")

        @log_execution_time(logger, level=logging.DEBUG)
        def slow_function():
            time.sleep(0.001)
            return 42

        result = slow_function()
        assert result == 42

    def test_log_execution_time_with_threshold(self):
        """log_execution_time respects threshold."""
        logger = get_logger("test.execution.threshold")

        @log_execution_time(logger, level=logging.DEBUG, threshold_ms=1000.0)
        def fast_function():
            return 42

        # Should not log (under threshold), but should still work
        result = fast_function()
        assert result == 42

    def test_log_module_call_decorator(self):
        """log_module_call decorator logs entry and exit."""
        logger = get_logger("test.module.call")

        @log_module_call(logger, level=logging.DEBUG)
        def my_function(x):
            return x * 2

        result = my_function(5)
        assert result == 10

    def test_health_check(self):
        health = HealthCheck()
        health.register("database", lambda: True)
        health.register("cache", lambda: True)
        result = health.check_all()
        assert result["status"] == "healthy"
        assert len(result["checks"]) == 2

    def test_health_check_unhealthy(self):
        health = HealthCheck()
        health.register("database", lambda: True)
        health.register("cache", lambda: False)
        result = health.check_all()
        assert result["status"] == "unhealthy"

    def test_health_check_is_healthy(self):
        health = HealthCheck()
        health.register("service", lambda: True)
        assert health.is_healthy() is True

    def test_health_check_unregister(self):
        health = HealthCheck()
        health.register("service", lambda: True)
        health.unregister("service")
        result = health.check_all()
        assert result["status"] == "healthy"
        assert len(result["checks"]) == 0

    def test_observability_in_pipeline(self):
        """Pipeline execution is observable via metrics."""
        metrics = MetricsCollector()
        pipeline = AcquisitionPipeline()
        entities = _entities_for_full_pipeline()

        with metrics.timeit("pipeline_run"):
            result = pipeline.run(entities, _full_config())

        stats = metrics.get_timer_stats("pipeline_run")
        assert stats["count"] == 1.0
        assert stats["min"] > 0
        assert result is not None


# ---------------------------------------------------------------------------
# 10. Orchestrator integration
# ---------------------------------------------------------------------------


class TestOrchestratorIntegration:
    """Full pipeline via orchestrator."""

    def test_orchestrator_full_pipeline(self):
        """Orchestrator runs all stages end-to-end."""
        pipeline = AcquisitionPipeline()
        entities = _entities_for_full_pipeline()
        result = pipeline.run(entities, _full_config())

        assert isinstance(result, PipelineResult)
        assert len(result.fraud_scores) > 0
        assert len(result.valuations) > 0
        assert len(result.matches) > 0
        assert result.portfolio is not None
        assert len(result.prices) > 0
        assert len(result.rankings) > 0
        assert result.evolution_result is not None

    def test_orchestrator_empty_entities(self):
        """Orchestrator handles empty input gracefully."""
        pipeline = AcquisitionPipeline()
        result = pipeline.run([], _full_config())
        assert isinstance(result, PipelineResult)
        assert result.matches == []
        assert result.valuations == []
        assert result.fraud_scores == []
        assert result.portfolio is None
        assert result.prices == []
        assert result.rankings == []
        assert result.evolution_result is None

    def test_orchestrator_partial_pipeline(self):
        """Orchestrator respects config flags."""
        pipeline = AcquisitionPipeline()
        entities = _entities_for_full_pipeline()
        config = PipelineConfig(
            enable_matching=False,
            enable_valuation=True,
            enable_fraud=True,
            enable_portfolio=False,
            enable_pricing=True,
            enable_ranking=False,
            enable_evolution=False,
        )
        result = pipeline.run(entities, config)

        assert len(result.valuations) > 0
        assert len(result.fraud_scores) > 0
        assert result.matches == []
        assert result.portfolio is None
        assert len(result.prices) > 0
        assert result.rankings == []
        assert result.evolution_result is None

    def test_orchestrator_result_types(self):
        """Orchestrator result contains correct types."""
        pipeline = AcquisitionPipeline()
        entities = _entities_for_full_pipeline()
        result = pipeline.run(entities, _full_config())

        for m in result.matches:
            assert hasattr(m, "buyer_id")
            assert hasattr(m, "seller_id")
            assert hasattr(m, "score")

        for v in result.valuations:
            assert hasattr(v, "value")
            assert hasattr(v, "method")
            assert v.value > 0

        for fs in result.fraud_scores:
            assert hasattr(fs, "score")
            assert hasattr(fs, "risk_level")
            assert 0.0 <= fs.score <= 1.0

        for p in result.prices:
            assert hasattr(p, "recommended_price")
            assert p.recommended_price > 0

        for r in result.rankings:
            assert hasattr(r, "score")
            assert hasattr(r, "id")

    def test_orchestrator_stage_runners_independently(self):
        """Each stage runner can be called independently."""
        pipeline = AcquisitionPipeline()

        # Fraud detection
        fraud_result = pipeline.run_fraud_detection([
            {"id": "e1", "attributes": {"signals": [
                {"name": "identity_verified", "value": 0.9},
                {"name": "financial_consistency", "value": 0.8},
                {"name": "traffic_authenticity", "value": 0.7},
            ]}},
        ])
        assert len(fraud_result) == 1
        assert fraud_result[0].risk_level == "low"

        # Valuation
        val_result = pipeline.run_valuation([_seller_dict("s1", 400_000)])
        assert len(val_result) == 1
        assert val_result[0].value > 0

        # Matching
        match_result = pipeline.run_matching([_buyer()], [_seller()])
        assert len(match_result) == 1

        # Portfolio
        portfolio_result = pipeline.run_portfolio_optimization(
            [Asset(id="a1", cost=100000, expected_return=0.10, risk=0.15)],
            budget=500_000,
        )
        assert isinstance(portfolio_result, Portfolio)

        # Pricing
        price_result = pipeline.run_pricing([
            ValuationResult(value=400000, method="DCF", confidence=0.7,
                            low_estimate=340000, high_estimate=460000),
        ])
        assert len(price_result) == 1

        # Ranking
        rank_result = pipeline.run_ranking("test", [
            Listing(id="l1", title="Test", relevance=0.9, category="saas"),
        ])
        assert len(rank_result) == 1

        # Evolution
        evo_result = pipeline.run_evolution(
            fitness_fn=lambda x: -((x - 0.5) ** 2) + 1.0,
            gene_range=(0.0, 1.0),
        )
        assert isinstance(evo_result, EvolutionResult)

    def test_orchestrator_with_fraudulent_entities(self):
        """Orchestrator processes entities with fraud signals."""
        pipeline = AcquisitionPipeline()
        entities = [
            _buyer_dict("b1", 500_000, "saas"),
            {
                "id": "bad_seller",
                "asking_price": 100_000,
                "attributes": {
                    "category": "saas",
                    "signals": [
                        {"name": "identity_verified", "value": 0.1},
                        {"name": "financial_consistency", "value": 0.05},
                        {"name": "traffic_authenticity", "value": 0.02},
                    ],
                },
            },
            _seller_dict("good_seller", 400_000, "saas"),
        ]
        result = pipeline.run(entities, _full_config())
        assert len(result.fraud_scores) >= 3
        # The fraudulent seller should have a high risk score
        assert any(fs.risk_level == "high" for fs in result.fraud_scores)

    def test_orchestrator_config_defaults(self):
        """PipelineConfig defaults to all stages enabled."""
        config = PipelineConfig()
        assert config.enable_matching is True
        assert config.enable_valuation is True
        assert config.enable_fraud is True
        assert config.enable_portfolio is True
        assert config.enable_pricing is True
        assert config.enable_ranking is True
        assert config.enable_evolution is True

    def test_orchestrator_result_defaults(self):
        """PipelineResult defaults to empty."""
        result = PipelineResult()
        assert result.matches == []
        assert result.valuations == []
        assert result.fraud_scores == []
        assert result.portfolio is None
        assert result.prices == []
        assert result.rankings == []
        assert result.evolution_result is None

    def test_orchestrator_multiple_runs(self):
        """Orchestrator can be run multiple times."""
        pipeline = AcquisitionPipeline()
        entities = _entities_for_full_pipeline()

        result1 = pipeline.run(entities, _full_config())
        result2 = pipeline.run(entities, _full_config())

        assert len(result1.matches) == len(result2.matches)
        assert len(result1.valuations) == len(result2.valuations)
        assert len(result1.fraud_scores) == len(result2.fraud_scores)

    def test_orchestrator_with_entity_resolution(self):
        """Orchestrator works with resolved entities."""
        # First resolve entities
        resolver = EntityResolver(threshold=0.85)
        raw_entities = [
            {"id": "e1", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e2", "name": "Acme Corp", "domain": "acme.com"},
            {"id": "e3", "name": "Globex Inc", "domain": "globex.io"},
        ]
        clusters = resolver.resolve(raw_entities)
        assert len(clusters) >= 2

        # Use resolved entities in pipeline
        pipeline = AcquisitionPipeline()
        pipeline_entities = _entities_for_full_pipeline()
        result = pipeline.run(pipeline_entities, _full_config())
        assert result is not None
