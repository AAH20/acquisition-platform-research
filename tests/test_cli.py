"""Tests for the acquisition platform CLI (`acq` / `python -m acquisition_platform`).

TDD suite covering every CLI command with valid input, error handling for
invalid input, and help output.
"""
from __future__ import annotations

import json
import random

import pytest

from acquisition_platform.__main__ import main

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run(argv: list[str]) -> int:
    """Invoke the CLI with an explicit argv list and return the exit code."""
    return main(argv)


def _write(path, data) -> str:
    path.write_text(json.dumps(data))
    return str(path)


@pytest.fixture()
def config_path(tmp_path):
    """An isolated config file path for `acq config` tests."""
    return str(tmp_path / "acq_config.json")


# ---------------------------------------------------------------------------
# Help / usage
# ---------------------------------------------------------------------------


class TestHelpOutput:
    def test_top_level_help_lists_commands(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0
        out = capsys.readouterr().out
        for cmd in [
            "match",
            "value",
            "fraud-check",
            "optimize",
            "price",
            "resolve",
            "rank",
            "evolve",
            "benchmark",
            "config",
        ]:
            assert cmd in out

    def test_subcommand_help(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["value", "--help"])
        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert "--fcf" in out
        assert "--discount" in out

    def test_no_command_is_an_error(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code == 2


# ---------------------------------------------------------------------------
# match
# ---------------------------------------------------------------------------


class TestMatchCommand:
    def test_match_valid(self, tmp_path, capsys):
        buyers = _write(
            tmp_path / "buyers.json",
            [{"id": "b1", "budget": 100000, "preferences": {"category": "saas"}}],
        )
        sellers = _write(
            tmp_path / "sellers.json",
            [{"id": "s1", "asking_price": 80000, "attributes": {"category": "saas"}}],
        )
        code = run(["match", "--buyers-file", buyers, "--sellers-file", sellers])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["count"] == 1
        assert out["matches"][0]["buyer_id"] == "b1"
        assert out["matches"][0]["seller_id"] == "s1"

    def test_match_missing_file(self, tmp_path, capsys):
        sellers = _write(tmp_path / "sellers.json", [])
        code = run(
            [
                "match",
                "--buyers-file",
                str(tmp_path / "nope.json"),
                "--sellers-file",
                sellers,
            ]
        )
        assert code == 1
        assert "error" in capsys.readouterr().err.lower()

    def test_match_invalid_json(self, tmp_path, capsys):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json")
        sellers = _write(tmp_path / "sellers.json", [])
        code = run(
            ["match", "--buyers-file", str(bad), "--sellers-file", sellers]
        )
        assert code == 1
        assert "error" in capsys.readouterr().err.lower()


# ---------------------------------------------------------------------------
# value
# ---------------------------------------------------------------------------


class TestValueCommand:
    def test_ensemble_valuation(self, capsys):
        code = run(
            [
                "value",
                "--fcf", "100000",
                "--revenue", "200000",
                "--growth", "0.05",
                "--discount", "0.10",
                "--terminal-growth", "0.02",
                "--multiple", "3",
                "--years", "5",
            ]
        )
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["method"] == "Ensemble"
        assert out["value"] > 0
        assert 0.0 <= out["confidence"] <= 1.0

    def test_dcf_only(self, capsys):
        code = run(
            [
                "value",
                "--fcf", "100000",
                "--growth", "0.05",
                "--discount", "0.10",
                "--terminal-growth", "0.02",
                "--years", "5",
            ]
        )
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["method"] == "DCF"
        assert out["value"] > 0

    def test_comps_only(self, capsys):
        code = run(["value", "--revenue", "200000", "--multiple", "3"])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["method"] == "Comps"
        assert out["value"] == pytest.approx(600000.0)

    def test_missing_required_combo_is_error(self, capsys):
        code = run(["value", "--fcf", "100000"])
        assert code == 1
        assert "error" in capsys.readouterr().err.lower()


# ---------------------------------------------------------------------------
# fraud-check
# ---------------------------------------------------------------------------


class TestFraudCheckCommand:
    def test_fraud_check_valid(self, capsys):
        signals = json.dumps(
            [
                ["identity_verified", 0.9],
                ["financial_consistency", 0.8],
                ["traffic_authenticity", 0.7],
            ]
        )
        code = run(["fraud-check", "--signals", signals])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert 0.0 <= out["score"] <= 1.0
        assert out["risk_level"] in {"low", "medium", "high"}
        assert out["confidence"] == pytest.approx(1.0)

    def test_fraud_check_dict_form(self, capsys):
        signals = json.dumps(
            [{"name": "identity_verified", "value": 0.1}]
        )
        code = run(["fraud-check", "--signals", signals])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["score"] >= 0.0

    def test_fraud_check_invalid_json_is_error(self, capsys):
        code = run(["fraud-check", "--signals", "{not json}"])
        assert code == 1
        assert "error" in capsys.readouterr().err.lower()

    def test_fraud_check_bad_shape_is_error(self, capsys):
        code = run(["fraud-check", "--signals", json.dumps({"a": 1})])
        assert code == 1
        assert "error" in capsys.readouterr().err.lower()


# ---------------------------------------------------------------------------
# optimize
# ---------------------------------------------------------------------------


class TestOptimizeCommand:
    def test_optimize_valid(self, tmp_path, capsys):
        assets = _write(
            tmp_path / "assets.json",
            [
                {"id": "a1", "cost": 30000, "expected_return": 0.2, "risk": 0.1, "sector": "saas"},
                {"id": "a2", "cost": 40000, "expected_return": 0.15, "risk": 0.2, "sector": "ecom"},
                {"id": "a3", "cost": 50000, "expected_return": 0.3, "risk": 0.3, "sector": "saas"},
            ],
        )
        code = run(
            [
                "optimize",
                "--budget", "100000",
                "--max-assets", "2",
                "--assets-file", assets,
            ]
        )
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["count"] <= 2
        assert out["count"] >= 1
        assert out["expected_return"] >= 0

    def test_optimize_missing_file(self, tmp_path, capsys):
        code = run(
            [
                "optimize",
                "--budget", "100000",
                "--max-assets", "2",
                "--assets-file", str(tmp_path / "nope.json"),
            ]
        )
        assert code == 1
        assert "error" in capsys.readouterr().err.lower()


# ---------------------------------------------------------------------------
# price
# ---------------------------------------------------------------------------


class TestPriceCommand:
    def test_price_valid(self, capsys):
        code = run(
            [
                "price",
                "--base-value", "100000",
                "--demand", "0.8",
                "--competition", "0.3",
                "--market", "bull",
            ]
        )
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["recommended_price"] > 0
        assert out["floor_price"] < out["ceiling_price"]

    def test_price_invalid_market_is_error(self, capsys):
        code = run(
            [
                "price",
                "--base-value", "100000",
                "--demand", "0.8",
                "--competition", "0.3",
                "--market", "sideways",
            ]
        )
        assert code == 1
        assert "error" in capsys.readouterr().err.lower()


# ---------------------------------------------------------------------------
# resolve
# ---------------------------------------------------------------------------


class TestResolveCommand:
    def test_resolve_valid(self, tmp_path, capsys):
        entities = _write(
            tmp_path / "entities.json",
            [
                {"name": "Acme Inc", "domain": "acme.com"},
                {"name": "Acme Inc", "domain": "acme.com"},
                {"name": "Globex", "domain": "globex.io"},
            ],
        )
        code = run(["resolve", "--entities-file", entities])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["count"] >= 1
        assert out["clusters"][0]["canonical_name"]
        assert out["clusters"][0]["size"] >= 1

    def test_resolve_missing_file(self, tmp_path, capsys):
        code = run(["resolve", "--entities-file", str(tmp_path / "nope.json")])
        assert code == 1
        assert "error" in capsys.readouterr().err.lower()


# ---------------------------------------------------------------------------
# rank
# ---------------------------------------------------------------------------


class TestRankCommand:
    def test_rank_valid(self, tmp_path, capsys):
        listings = _write(
            tmp_path / "listings.json",
            [
                {"id": "l1", "title": "SaaS A", "relevance": 0.9, "category": "saas"},
                {"id": "l2", "title": "SaaS B", "relevance": 0.8, "category": "saas"},
                {"id": "l3", "title": "Ecom C", "relevance": 0.5, "category": "ecom"},
            ],
        )
        code = run(["rank", "--query", "saas", "--listings-file", listings])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["query"] == "saas"
        assert len(out["rankings"]) == 3
        scores = [r["score"] for r in out["rankings"]]
        assert scores == sorted(scores, reverse=True)

    def test_rank_missing_file(self, tmp_path, capsys):
        code = run(
            ["rank", "--query", "saas", "--listings-file", str(tmp_path / "nope.json")]
        )
        assert code == 1
        assert "error" in capsys.readouterr().err.lower()


# ---------------------------------------------------------------------------
# evolve
# ---------------------------------------------------------------------------


class TestEvolveCommand:
    def test_evolve_valid(self, capsys):
        random.seed(42)
        code = run(
            [
                "evolve",
                "--fitness-fn", "-(x-3)**2 + 9",
                "--gene-range", "0,10",
                "--seed", "42",
                "--generations", "20",
                "--population-size", "50",
            ]
        )
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["best_fitness"] > 8.0
        assert out["population_size"] == 50
        assert "converged" in out

    def test_evolve_bad_expression_is_error(self, capsys):
        code = run(
            ["evolve", "--fitness-fn", "this is not python (", "--gene-range", "0,10"]
        )
        assert code == 1
        assert "error" in capsys.readouterr().err.lower()

    def test_evolve_bad_range_is_error(self, capsys):
        code = run(["evolve", "--fitness-fn", "x", "--gene-range", "10,0"])
        assert code == 1
        assert "error" in capsys.readouterr().err.lower()


# ---------------------------------------------------------------------------
# benchmark
# ---------------------------------------------------------------------------


class TestBenchmarkCommand:
    def test_benchmark_pass(self, capsys):
        code = run(
            ["benchmark", "--name", "accuracy", "--target", "0.9", "--actual", "0.95"]
        )
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["passed"] is True
        assert out["name"] == "accuracy"
        assert out["gap"] == pytest.approx(0.9 - 0.95)

    def test_benchmark_fail(self, capsys):
        code = run(
            ["benchmark", "--name", "accuracy", "--target", "0.9", "--actual", "0.85"]
        )
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["passed"] is False
        assert out["gap"] == pytest.approx(0.05)
        assert "Improve" in out["suggestion"]


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------


class TestConfigCommand:
    def test_config_show_defaults(self, config_path, capsys):
        code = run(["--config", config_path, "config", "show"])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert "entity_resolution" in out
        assert out["entity_resolution"]["threshold"] == pytest.approx(0.85)

    def test_config_set_then_show(self, config_path, capsys):
        code = run(
            ["--config", config_path, "config", "set", "entity_resolution.threshold", "0.9"]
        )
        assert code == 0
        capsys.readouterr()

        code = run(["--config", config_path, "config", "show"])
        assert code == 0
        out = json.loads(capsys.readouterr().out)
        assert out["entity_resolution"]["threshold"] == pytest.approx(0.9)

    def test_config_set_bad_path_is_error(self, config_path, capsys):
        code = run(
            ["--config", config_path, "config", "set", "a.b.c.d", "1"]
        )
        assert code == 1
        assert "error" in capsys.readouterr().err.lower()
