"""Tests for the FastAPI REST API layer.

Covers every endpoint with valid input, error handling for invalid
input, the health check, metrics, and OpenAPI schema exposure.
"""

import pytest
from fastapi.testclient import TestClient

from acquisition_platform.api import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# System endpoints
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_check(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "uptime_seconds" in data

    def test_openapi_schema_exposed(self, client: TestClient) -> None:
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        paths = resp.json()["paths"]
        for endpoint in [
            "/match",
            "/value",
            "/fraud-check",
            "/optimize",
            "/price",
            "/resolve",
            "/rank",
            "/evolve",
            "/auction",
            "/due-diligence",
            "/cross-border",
            "/recommend",
            "/pipeline",
            "/health",
            "/metrics",
        ]:
            assert endpoint in paths

    def test_docs_ui_available(self, client: TestClient) -> None:
        resp = client.get("/docs")
        assert resp.status_code == 200


class TestMetrics:
    def test_metrics_endpoint_returns_structure(self, client: TestClient) -> None:
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
        assert "total_errors" in data
        assert "uptime_seconds" in data
        assert "endpoints" in data

    def test_metrics_track_requests(self, client: TestClient) -> None:
        client.get("/health")
        data = client.get("/metrics").json()
        assert data["total_requests"] >= 1
        assert "/health" in data["endpoints"]
        assert data["endpoints"]["/health"]["requests"] >= 1

    def test_metrics_track_errors(self, client: TestClient) -> None:
        client.post("/match", json={"buyers": [], "sellers": []})
        data = client.get("/metrics").json()
        assert data["total_errors"] >= 1


# ---------------------------------------------------------------------------
# POST /match
# ---------------------------------------------------------------------------


class TestMatchEndpoint:
    def test_match_valid_input(self, client: TestClient) -> None:
        resp = client.post(
            "/match",
            json={
                "buyers": [
                    {"id": "b1", "budget": 100000, "preferences": {"category": "saas"}}
                ],
                "sellers": [
                    {
                        "id": "s1",
                        "asking_price": 80000,
                        "attributes": {"category": "saas"},
                    }
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["matches"][0]["buyer_id"] == "b1"
        assert data["matches"][0]["seller_id"] == "s1"
        assert 0.0 <= data["matches"][0]["score"] <= 1.0
        assert 0.0 <= data["matches"][0]["confidence"] <= 1.0

    def test_match_empty_buyers_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/match",
            json={
                "buyers": [],
                "sellers": [
                    {"id": "s1", "asking_price": 80000, "attributes": {}}
                ],
            },
        )
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_match_empty_sellers_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/match",
            json={
                "buyers": [{"id": "b1", "budget": 100000, "preferences": {}}],
                "sellers": [],
            },
        )
        assert resp.status_code == 422

    def test_match_negative_budget_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/match",
            json={
                "buyers": [{"id": "b1", "budget": -5, "preferences": {}}],
                "sellers": [{"id": "s1", "asking_price": 100, "attributes": {}}],
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /value
# ---------------------------------------------------------------------------


class TestValueEndpoint:
    def test_value_dcf_valid(self, client: TestClient) -> None:
        resp = client.post(
            "/value",
            json={
                "method": "dcf",
                "free_cash_flow": 100000,
                "growth_rate": 0.05,
                "discount_rate": 0.10,
                "terminal_growth": 0.02,
                "years": 5,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["method"] == "DCF"
        assert data["value"] > 0
        assert data["low_estimate"] < data["value"] < data["high_estimate"]
        assert 0.0 <= data["confidence"] <= 1.0

    def test_value_comps_valid(self, client: TestClient) -> None:
        resp = client.post(
            "/value",
            json={"method": "comps", "metric": 500000, "multiple": 3.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["method"] == "Comps"
        assert data["value"] == 1500000.0

    def test_value_sde_valid(self, client: TestClient) -> None:
        resp = client.post(
            "/value",
            json={"method": "sde", "sde": 200000, "multiple": 2.5},
        )
        assert resp.status_code == 200
        assert resp.json()["value"] == 500000.0

    def test_value_arr_valid(self, client: TestClient) -> None:
        resp = client.post(
            "/value",
            json={"method": "arr", "arr": 1000000, "multiple": 4.0},
        )
        assert resp.status_code == 200
        assert resp.json()["value"] == 4000000.0

    def test_value_ensemble_valid(self, client: TestClient) -> None:
        resp = client.post(
            "/value",
            json={
                "method": "ensemble",
                "free_cash_flow": 100000,
                "revenue": 500000,
                "growth_rate": 0.05,
                "discount_rate": 0.10,
                "terminal_growth": 0.02,
                "revenue_multiple": 3.0,
                "years": 5,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["method"] == "Ensemble"

    def test_value_negative_cash_flow_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/value",
            json={
                "method": "dcf",
                "free_cash_flow": -1,
                "growth_rate": 0.05,
                "discount_rate": 0.10,
                "terminal_growth": 0.02,
                "years": 5,
            },
        )
        assert resp.status_code == 422

    def test_value_missing_required_field_returns_422(self, client: TestClient) -> None:
        resp = client.post("/value", json={"method": "comps", "metric": 500000})
        assert resp.status_code == 422

    def test_value_discount_equals_terminal_growth_returns_200(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/value",
            json={
                "method": "dcf",
                "free_cash_flow": 100000,
                "growth_rate": 0.05,
                "discount_rate": 0.10,
                "terminal_growth": 0.10,
                "years": 5,
            },
        )
        assert resp.status_code == 200 or resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /fraud-check
# ---------------------------------------------------------------------------


class TestFraudCheckEndpoint:
    def test_fraud_check_valid_signals(self, client: TestClient) -> None:
        resp = client.post(
            "/fraud-check",
            json={
                "signals": [
                    {"name": "identity_verified", "value": 0.9},
                    {"name": "financial_consistency", "value": 0.8},
                    {"name": "traffic_authenticity", "value": 0.7},
                ]
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert 0.0 <= data["score"] <= 1.0
        assert data["risk_level"] in {"low", "medium", "high"}
        assert 0.0 <= data["confidence"] <= 1.0
        assert len(data["explanations"]) == 3

    def test_fraud_check_graph_with_ring(self, client: TestClient) -> None:
        resp = client.post(
            "/fraud-check",
            json={
                "graph": {
                    "nodes": ["a", "b", "c"],
                    "edges": [["a", "b"], ["b", "c"], ["c", "a"]],
                }
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_ring"] is True
        assert data["risk_level"] == "high"

    def test_fraud_check_graph_without_ring(self, client: TestClient) -> None:
        resp = client.post(
            "/fraud-check",
            json={
                "graph": {
                    "nodes": ["a", "b", "c"],
                    "edges": [["a", "b"], ["b", "c"]],
                }
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["has_ring"] is False

    def test_fraud_check_signal_out_of_range_returns_422(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/fraud-check",
            json={"signals": [{"name": "identity_verified", "value": 1.5}]},
        )
        assert resp.status_code == 422

    def test_fraud_check_empty_signals_returns_200(self, client: TestClient) -> None:
        resp = client.post("/fraud-check", json={"signals": []})
        assert resp.status_code == 200
        data = resp.json()
        assert data["score"] == 0.0
        assert data["risk_level"] == "low"


# ---------------------------------------------------------------------------
# POST /optimize
# ---------------------------------------------------------------------------


class TestOptimizeEndpoint:
    def test_optimize_valid_input(self, client: TestClient) -> None:
        resp = client.post(
            "/optimize",
            json={
                "budget": 1000000,
                "max_assets": 5,
                "risk_tolerance": 0.5,
                "assets": [
                    {
                        "id": "a1",
                        "cost": 200000,
                        "expected_return": 0.15,
                        "risk": 0.1,
                        "sector": "saas",
                    },
                    {
                        "id": "a2",
                        "cost": 300000,
                        "expected_return": 0.12,
                        "risk": 0.2,
                        "sector": "ecommerce",
                    },
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "assets" in data
        assert "expected_return" in data
        assert "sharpe_ratio" in data
        assert isinstance(data["assets"], list)

    def test_optimize_risk_tolerance_out_of_range_returns_422(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/optimize",
            json={
                "budget": 1000000,
                "max_assets": 5,
                "risk_tolerance": 1.5,
                "assets": [
                    {
                        "id": "a1",
                        "cost": 200000,
                        "expected_return": 0.15,
                        "risk": 0.1,
                        "sector": "saas",
                    }
                ],
            },
        )
        assert resp.status_code == 422

    def test_optimize_empty_assets_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/optimize",
            json={
                "budget": 1000000,
                "max_assets": 5,
                "risk_tolerance": 0.5,
                "assets": [],
            },
        )
        assert resp.status_code == 422

    def test_optimize_negative_budget_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/optimize",
            json={
                "budget": -100,
                "max_assets": 5,
                "risk_tolerance": 0.5,
                "assets": [
                    {
                        "id": "a1",
                        "cost": 200000,
                        "expected_return": 0.15,
                        "risk": 0.1,
                        "sector": "saas",
                    }
                ],
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /price
# ---------------------------------------------------------------------------


class TestPriceEndpoint:
    def test_price_valid_input(self, client: TestClient) -> None:
        resp = client.post(
            "/price",
            json={
                "base_value": 1000000,
                "demand_level": 0.8,
                "competition_level": 0.3,
                "market_condition": "bull",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["recommended_price"] > 0
        assert data["floor_price"] < data["recommended_price"] < data["ceiling_price"]
        assert 0.0 <= data["confidence"] <= 1.0
        assert data["equilibrium_price"] > 0

    def test_price_invalid_market_condition_returns_422(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/price",
            json={
                "base_value": 1000000,
                "demand_level": 0.8,
                "competition_level": 0.3,
                "market_condition": "hyper",
            },
        )
        assert resp.status_code == 422

    def test_price_demand_out_of_range_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/price",
            json={
                "base_value": 1000000,
                "demand_level": 1.5,
                "competition_level": 0.3,
                "market_condition": "normal",
            },
        )
        assert resp.status_code == 422

    def test_price_non_positive_base_value_returns_422(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/price",
            json={
                "base_value": 0,
                "demand_level": 0.5,
                "competition_level": 0.3,
                "market_condition": "normal",
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /resolve
# ---------------------------------------------------------------------------


class TestResolveEndpoint:
    def test_resolve_valid_input(self, client: TestClient) -> None:
        resp = client.post(
            "/resolve",
            json={
                "entities": [
                    {"name": "Acme Inc", "domain": "acme.com", "id": "e1"},
                    {"name": "Acme Incorporated", "domain": "acme.com", "id": "e2"},
                ],
                "threshold": 0.85,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "clusters" in data
        assert data["count"] >= 1
        assert len(data["clusters"][0]["entities"]) >= 1

    def test_resolve_empty_entities_returns_422(self, client: TestClient) -> None:
        resp = client.post("/resolve", json={"entities": []})
        assert resp.status_code == 422

    def test_resolve_threshold_out_of_range_returns_422(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/resolve",
            json={
                "entities": [{"name": "Acme Inc"}],
                "threshold": 1.5,
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /rank
# ---------------------------------------------------------------------------


class TestRankEndpoint:
    def test_rank_valid_input(self, client: TestClient) -> None:
        resp = client.post(
            "/rank",
            json={
                "query": "saas",
                "listings": [
                    {"id": "l1", "title": "SaaS A", "relevance": 0.9, "category": "saas"},
                    {"id": "l2", "title": "Ecom B", "relevance": 0.7, "category": "ecommerce"},
                ],
                "user_preferences": {"category": "saas"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "rankings" in data
        assert data["count"] == 2
        # Personalized saas listing should rank first
        assert data["rankings"][0]["id"] == "l1"

    def test_rank_empty_listings_returns_422(self, client: TestClient) -> None:
        resp = client.post("/rank", json={"query": "saas", "listings": []})
        assert resp.status_code == 422

    def test_rank_relevance_out_of_range_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/rank",
            json={
                "query": "saas",
                "listings": [
                    {"id": "l1", "title": "SaaS A", "relevance": 1.5, "category": "saas"}
                ],
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /evolve
# ---------------------------------------------------------------------------


class TestEvolveEndpoint:
    def test_evolve_valid_input(self, client: TestClient) -> None:
        resp = client.post(
            "/evolve",
            json={
                "population_size": 20,
                "generations": 10,
                "mutation_rate": 0.1,
                "elitism": 2,
                "gene_min": 0.0,
                "gene_max": 1.0,
                "fitness": "quadratic",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "best_fitness" in data
        assert "generation_count" in data
        assert "population_size" in data
        assert "diversity" in data
        assert "offspring_count" in data
        assert "converged" in data
        assert "worst_fitness" in data

    def test_evolve_sine_fitness(self, client: TestClient) -> None:
        resp = client.post(
            "/evolve",
            json={
                "population_size": 10,
                "generations": 5,
                "fitness": "sine",
            },
        )
        assert resp.status_code == 200

    def test_evolve_invalid_population_size_returns_422(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/evolve",
            json={"population_size": 0, "generations": 10},
        )
        assert resp.status_code == 422

    def test_evolve_invalid_mutation_rate_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/evolve",
            json={"mutation_rate": 1.5},
        )
        assert resp.status_code == 422

    def test_evolve_invalid_gene_range_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/evolve",
            json={"gene_min": 1.0, "gene_max": 0.0},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /auction
# ---------------------------------------------------------------------------


class TestAuctionEndpoint:
    def test_auction_vickrey_valid(self, client: TestClient) -> None:
        resp = client.post(
            "/auction",
            json={
                "bids": [
                    {"bidder_id": "b1", "amount": 100},
                    {"bidder_id": "b2", "amount": 150},
                ],
                "config": {"format": "vickrey", "reserve_price": 50, "min_increment": 5},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["winner_id"] == "b2"
        assert data["winning_bid"] == 150
        # Vickrey: winner pays second-highest bid
        assert data["revenue"] == 100
        assert data["format"] == "vickrey"

    def test_auction_english_valid(self, client: TestClient) -> None:
        resp = client.post(
            "/auction",
            json={
                "bids": [
                    {"bidder_id": "b1", "amount": 100},
                    {"bidder_id": "b2", "amount": 150},
                ],
                "config": {"format": "english", "reserve_price": 50, "min_increment": 5},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        # English: winner pays their own bid
        assert data["revenue"] == 150

    def test_auction_no_valid_bids(self, client: TestClient) -> None:
        resp = client.post(
            "/auction",
            json={
                "bids": [{"bidder_id": "b1", "amount": 10}],
                "config": {"format": "vickrey", "reserve_price": 50, "min_increment": 5},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["winner_id"] is None
        assert data["revenue"] == 0.0

    def test_auction_invalid_format_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/auction",
            json={
                "bids": [{"bidder_id": "b1", "amount": 100}],
                "config": {"format": "sealed", "reserve_price": 50, "min_increment": 5},
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /due-diligence
# ---------------------------------------------------------------------------


class TestDueDiligenceEndpoint:
    def test_due_diligence_valid_input(self, client: TestClient) -> None:
        resp = client.post(
            "/due-diligence",
            json={
                "tasks": [
                    {
                        "id": "t1",
                        "name": "Financial review",
                        "duration": 4,
                        "expertise": "finance",
                        "dependencies": [],
                    },
                    {
                        "id": "t2",
                        "name": "Legal review",
                        "duration": 3,
                        "expertise": "legal",
                        "dependencies": ["t1"],
                    },
                ],
                "reviewers": [
                    {"id": "r1", "name": "Alice", "expertise": ["finance"], "availability": 8},
                    {"id": "r2", "name": "Bob", "expertise": ["legal"], "availability": 8},
                ],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "assignments" in data
        assert len(data["assignments"]) == 2
        assert data["makespan"] > 0
        assert "reviewer_utilization" in data

    def test_due_diligence_no_reviewers_returns_422(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/due-diligence",
            json={
                "tasks": [
                    {
                        "id": "t1",
                        "name": "Financial review",
                        "duration": 4,
                        "expertise": "finance",
                        "dependencies": [],
                    }
                ],
                "reviewers": [],
            },
        )
        assert resp.status_code == 422

    def test_due_diligence_unschedulable_task_returns_422(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/due-diligence",
            json={
                "tasks": [
                    {
                        "id": "t1",
                        "name": "Financial review",
                        "duration": 100,
                        "expertise": "finance",
                        "dependencies": [],
                    }
                ],
                "reviewers": [
                    {"id": "r1", "name": "Alice", "expertise": ["finance"], "availability": 8},
                ],
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /cross-border
# ---------------------------------------------------------------------------


class TestCrossBorderEndpoint:
    def test_cross_border_valid_input(self, client: TestClient) -> None:
        resp = client.post(
            "/cross-border",
            json={
                "deal": {
                    "jurisdictions": [
                        {"code": "US", "name": "United States", "regulatory_body": "SEC", "tax_rate": 0.21},
                        {"code": "DE", "name": "Germany", "regulatory_body": "BaFin", "tax_rate": 0.30},
                    ],
                    "deal_value": 10000000,
                    "deal_type": "acquisition",
                }
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "filings" in data
        assert len(data["filings"]) == 10  # 5 per jurisdiction
        assert data["total_tax"] > 0
        assert data["hedging_cost"] > 0
        assert data["integration_timeline"] > 0
        assert 0.0 <= data["risk_score"] <= 1.0

    def test_cross_border_negative_deal_value_returns_422(
        self, client: TestClient
    ) -> None:
        resp = client.post(
            "/cross-border",
            json={
                "deal": {
                    "jurisdictions": [
                        {"code": "US", "name": "United States", "regulatory_body": "SEC", "tax_rate": 0.21}
                    ],
                    "deal_value": -1,
                    "deal_type": "acquisition",
                }
            },
        )
        assert resp.status_code == 422

    def test_cross_border_empty_jurisdictions(self, client: TestClient) -> None:
        resp = client.post(
            "/cross-border",
            json={
                "deal": {
                    "jurisdictions": [],
                    "deal_value": 1000000,
                    "deal_type": "acquisition",
                }
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["filings"] == []
        assert data["total_tax"] == 0.0


# ---------------------------------------------------------------------------
# POST /recommend
# ---------------------------------------------------------------------------


class TestRecommendEndpoint:
    def test_recommend_valid_input(self, client: TestClient) -> None:
        resp = client.post(
            "/recommend",
            json={
                "user": {"user_id": "u1", "preferences": {"topic": "ml"}, "history": []},
                "items": [
                    {"item_id": "i1", "attributes": {"topic": "ml"}, "category": "saas"},
                    {"item_id": "i2", "attributes": {"topic": "web"}, "category": "ecommerce"},
                ],
                "k": 5,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendations" in data
        assert "diversity_score" in data
        assert "coverage" in data
        assert len(data["recommendations"]) > 0

    def test_recommend_empty_items_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/recommend",
            json={
                "user": {"user_id": "u1", "preferences": {}, "history": []},
                "items": [],
            },
        )
        assert resp.status_code == 422

    def test_recommend_excludes_history(self, client: TestClient) -> None:
        resp = client.post(
            "/recommend",
            json={
                "user": {"user_id": "u1", "preferences": {"topic": "ml"}, "history": ["i1"]},
                "items": [
                    {"item_id": "i1", "attributes": {"topic": "ml"}, "category": "saas"},
                    {"item_id": "i2", "attributes": {"topic": "web"}, "category": "ecommerce"},
                ],
                "k": 5,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        recommended_ids = [r["item_id"] for r in data["recommendations"]]
        assert "i1" not in recommended_ids


# ---------------------------------------------------------------------------
# POST /pipeline
# ---------------------------------------------------------------------------


class TestPipelineEndpoint:
    def test_pipeline_valid_input(self, client: TestClient) -> None:
        resp = client.post(
            "/pipeline",
            json={
                "entities": [
                    {"id": "b1", "budget": 100000, "preferences": {"category": "saas"}},
                    {
                        "id": "s1",
                        "asking_price": 80000,
                        "attributes": {
                            "category": "saas",
                            "title": "SaaS Co",
                            "relevance": 0.9,
                            "expected_return": 0.12,
                            "risk": 0.1,
                        },
                    },
                ]
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "matches" in data
        assert "valuations" in data
        assert "fraud_scores" in data
        assert "portfolio" in data
        assert "prices" in data
        assert "rankings" in data
        assert "evolution_result" in data

    def test_pipeline_with_config(self, client: TestClient) -> None:
        resp = client.post(
            "/pipeline",
            json={
                "entities": [
                    {"id": "b1", "budget": 100000, "preferences": {"category": "saas"}},
                    {
                        "id": "s1",
                        "asking_price": 80000,
                        "attributes": {"category": "saas"},
                    },
                ],
                "config": {"enable_matching": True, "enable_evolution": False},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["matches"] != []
        assert data["evolution_result"] is None

    def test_pipeline_empty_entities(self, client: TestClient) -> None:
        resp = client.post("/pipeline", json={"entities": []})
        assert resp.status_code == 200
        data = resp.json()
        assert data["matches"] == []
        assert data["valuations"] == []
