"""Command-line interface for the Acquisition Platform.

Entry point for both the installed ``acquisition-platform`` console script and
``python -m acquisition_platform``.

The CLI exposes every solver in the package through a small, uniform argparse
surface. JSON is used for structured input (files or inline) and JSON is always
written to stdout, so commands compose cleanly in shell pipelines and CI.

Exit codes
----------
0
    Success.
1
    A handled runtime/input error (bad file, malformed JSON, invalid argument
    combination). A message prefixed with ``error:`` is written to stderr.
2
    argparse usage error (missing/invalid flag, unknown command). Emitted by
    argparse itself via ``SystemExit``.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
import random
import sys
from pathlib import Path
from typing import Any, Callable

from acquisition_platform.dynamic_pricing import PricingEngine
from acquisition_platform.entity_resolution import EntityResolver
from acquisition_platform.evolution import Benchmark, EvolutionEngine
from acquisition_platform.fraud_detection import FraudDetector, FraudSignal
from acquisition_platform.matching import Buyer, BuyerSellerMatcher, Seller
from acquisition_platform.portfolio_optimizer import Asset, PortfolioOptimizer
from acquisition_platform.search_ranking import Listing, SearchRanker
from acquisition_platform.valuation import ValuationEngine

PROG = "acq"

#: Built-in configuration schema. ``acq config show`` returns these defaults
#: merged with any persisted overrides; ``acq config set`` may only mutate
#: keys that already exist here.
DEFAULT_CONFIG: dict[str, Any] = {
    "entity_resolution": {
        "threshold": 0.85,
    },
    "portfolio_optimization": {
        "max_assets": 10,
        "risk_tolerance": 0.5,
    },
    "dynamic_pricing": {
        "market_multipliers": {"bull": 1.15, "bear": 0.85, "normal": 1.0},
    },
    "search_ranking": {
        "diversity_factor_subsequent": 0.7,
        "personalization_factor": 1.3,
    },
    "fraud_detection": {
        "default_weight": 0.1,
        "total_expected_signals": 3,
    },
    "evolution": {
        "population_size": 50,
        "generations": 20,
        "mutation_rate": 0.1,
        "elitism": 2,
    },
}


class CLIError(Exception):
    """A handled, user-facing CLI error (reported with exit code 1)."""


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def _load_json_file(path: str) -> Any:
    """Read and parse a JSON file, raising :class:`CLIError` on failure."""
    p = Path(path)
    if not p.is_file():
        raise CLIError(f"file not found: {path}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CLIError(f"invalid JSON in {path}: {exc}") from exc


def _emit(obj: Any) -> None:
    """Write a JSON object to stdout."""
    json.dump(obj, sys.stdout, indent=2, sort_keys=True, default=str)
    sys.stdout.write("\n")


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CLIError(f"{label} must be a JSON object, got {type(value).__name__}")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise CLIError(f"{label} must be a JSON array, got {type(value).__name__}")
    return value


def _require_finite(value: float, label: str) -> float:
    if value is None or not math.isfinite(value):
        raise CLIError(f"{label} must be a finite number")
    return value


# ---------------------------------------------------------------------------
# Config store
# ---------------------------------------------------------------------------


def _resolve_config_path(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    env = os.environ.get("ACQ_CONFIG")
    if env:
        return Path(env)
    return Path.home() / ".acq" / "config.json"


def _load_config(path: Path) -> dict[str, Any]:
    """Return DEFAULT_CONFIG deep-merged with the persisted file (if any)."""
    merged = copy.deepcopy(DEFAULT_CONFIG)
    if not path.is_file():
        return merged
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CLIError(f"invalid config file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CLIError(f"config file {path} must contain a JSON object")
    for key, value in data.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def _save_config(path: Path, config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, sort_keys=True), encoding="utf-8")


def _coerce_config_value(raw: str) -> Any:
    """Parse a CLI string as JSON, falling back to a plain string."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _config_set(config: dict[str, Any], dotted_key: str, raw_value: str) -> Any:
    parts = dotted_key.split(".")
    node: Any = config
    for part in parts[:-1]:
        if not isinstance(node, dict) or part not in node:
            raise CLIError(f"unknown config key: {dotted_key}")
        node = node[part]
    leaf = parts[-1]
    if not isinstance(node, dict) or leaf not in node:
        raise CLIError(f"unknown config key: {dotted_key}")
    node[leaf] = _coerce_config_value(raw_value)
    return node[leaf]


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def _cmd_match(args: argparse.Namespace) -> int:
    buyers_raw = _require_list(_load_json_file(args.buyers_file), "buyers")
    sellers_raw = _require_list(_load_json_file(args.sellers_file), "sellers")

    buyers = [
        Buyer(
            id=str(b["id"]),
            budget=float(b["budget"]),
            preferences=dict(b.get("preferences", {})),
        )
        for b in buyers_raw
    ]
    sellers = [
        Seller(
            id=str(s["id"]),
            asking_price=float(s["asking_price"]),
            attributes=dict(s.get("attributes", {})),
        )
        for s in sellers_raw
    ]

    matches = BuyerSellerMatcher().match(buyers, sellers)
    _emit(
        {
            "count": len(matches),
            "matches": [
                {
                    "buyer_id": m.buyer_id,
                    "seller_id": m.seller_id,
                    "score": m.score,
                    "confidence": m.confidence,
                }
                for m in matches
            ],
        }
    )
    return 0


def _cmd_value(args: argparse.Namespace) -> int:
    engine = ValuationEngine()
    has_fcf = args.fcf is not None

    if has_fcf:
        for name in ("growth", "discount", "terminal_growth", "years"):
            if getattr(args, name) is None:
                raise CLIError(
                    f"--{name.replace('_', '-')} is required when --fcf is provided"
                )
        if args.discount <= args.terminal_growth:
            raise CLIError("--discount must be greater than --terminal-growth")
        if args.years < 1:
            raise CLIError("--years must be >= 1")

        if args.revenue is not None and args.multiple is not None:
            result = engine.ensemble_valuation(
                free_cash_flow=args.fcf,
                revenue=args.revenue,
                growth_rate=args.growth,
                discount_rate=args.discount,
                terminal_growth=args.terminal_growth,
                revenue_multiple=args.multiple,
                years=args.years,
            )
        elif args.revenue is None and args.multiple is None:
            result = engine.dcf_valuation(
                free_cash_flow=args.fcf,
                growth_rate=args.growth,
                discount_rate=args.discount,
                terminal_growth=args.terminal_growth,
                years=args.years,
            )
        else:
            raise CLIError("--revenue and --multiple must be provided together")
    elif args.revenue is not None and args.multiple is not None:
        result = engine.comparable_valuation(metric=args.revenue, multiple=args.multiple)
    else:
        raise CLIError(
            "provide --fcf (DCF/ensemble) or both --revenue and --multiple (comps)"
        )

    _emit(
        {
            "value": result.value,
            "method": result.method,
            "confidence": result.confidence,
            "low_estimate": result.low_estimate,
            "high_estimate": result.high_estimate,
        }
    )
    return 0


def _parse_signals(text: str) -> list[FraudSignal]:
    """Parse signals from a JSON string.

    Accepts a JSON array of ``[name, value]`` pairs or a JSON array of
    ``{"name": ..., "value": ...}`` objects.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CLIError(f"--signals is not valid JSON: {exc}") from exc

    if not isinstance(data, list):
        raise CLIError(
            "--signals must be a JSON array of [name, value] pairs or "
            "{name, value} objects"
        )

    signals: list[FraudSignal] = []
    for item in data:
        if isinstance(item, dict) and "name" in item and "value" in item:
            signals.append(
                FraudSignal(name=str(item["name"]), value=float(item["value"]))
            )
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            signals.append(FraudSignal(name=str(item[0]), value=float(item[1])))
        else:
            raise CLIError(
                "each signal must be a [name, value] pair or a {name, value} object"
            )
    return signals


def _cmd_fraud_check(args: argparse.Namespace) -> int:
    signals = _parse_signals(args.signals)
    result = FraudDetector().score(signals)
    _emit(
        {
            "score": result.score,
            "risk_level": result.risk_level,
            "confidence": result.confidence,
            "explanations": result.explanations,
        }
    )
    return 0


def _cmd_optimize(args: argparse.Namespace) -> int:
    assets_raw = _require_list(_load_json_file(args.assets_file), "assets")
    assets = [
        Asset(
            id=str(a["id"]),
            cost=float(a["cost"]),
            expected_return=float(a["expected_return"]),
            risk=float(a["risk"]),
            sector=str(a.get("sector", "")),
        )
        for a in assets_raw
    ]

    if args.budget < 0:
        raise CLIError("--budget must be >= 0")
    if args.max_assets < 1:
        raise CLIError("--max-assets must be >= 1")

    optimizer = PortfolioOptimizer(budget=args.budget, max_assets=args.max_assets)
    portfolio = optimizer.optimize(assets, risk_tolerance=args.risk_tolerance)
    _emit(
        {
            "count": len(portfolio.assets),
            "expected_return": portfolio.expected_return,
            "sharpe_ratio": portfolio.sharpe_ratio,
            "assets": [
                {
                    "id": a.id,
                    "cost": a.cost,
                    "expected_return": a.expected_return,
                    "risk": a.risk,
                    "sector": a.sector,
                }
                for a in portfolio.assets
            ],
        }
    )
    return 0


def _cmd_price(args: argparse.Namespace) -> int:
    valid_markets = {"bull", "bear", "normal"}
    if args.market not in valid_markets:
        raise CLIError(
            f"invalid --market {args.market!r}; choose one of {sorted(valid_markets)}"
        )
    if not 0.0 <= args.demand <= 1.0:
        raise CLIError("--demand must be in [0, 1]")
    if not 0.0 <= args.competition <= 1.0:
        raise CLIError("--competition must be in [0, 1]")

    result = PricingEngine().recommend_price(
        base_value=args.base_value,
        demand_level=args.demand,
        competition_level=args.competition,
        market_condition=args.market,
    )
    _emit(
        {
            "recommended_price": result.recommended_price,
            "confidence": result.confidence,
            "floor_price": result.floor_price,
            "ceiling_price": result.ceiling_price,
            "equilibrium_price": result.equilibrium_price,
        }
    )
    return 0


def _cmd_resolve(args: argparse.Namespace) -> int:
    entities = _require_list(_load_json_file(args.entities_file), "entities")
    for entity in entities:
        _require_mapping(entity, "each entity")

    resolver = EntityResolver(threshold=args.threshold)
    clusters = resolver.resolve(entities)
    _emit(
        {
            "count": len(clusters),
            "comparison_count": resolver.comparison_count,
            "clusters": [
                {
                    "canonical_name": c.canonical_name,
                    "size": len(c.entities),
                    "entities": c.entities,
                }
                for c in clusters
            ],
        }
    )
    return 0


def _cmd_rank(args: argparse.Namespace) -> int:
    listings_raw = _require_list(_load_json_file(args.listings_file), "listings")
    listings = [
        Listing(
            id=str(item["id"]),
            title=str(item["title"]),
            relevance=float(item["relevance"]),
            category=str(item.get("category", "")),
        )
        for item in listings_raw
    ]

    prefs = {"category": args.category} if args.category else None
    ranked = SearchRanker().rank(query=args.query, listings=listings, user_preferences=prefs)
    _emit(
        {
            "query": args.query,
            "count": len(ranked),
            "rankings": [
                {
                    "id": r.id,
                    "title": r.title,
                    "score": r.score,
                    "category": r.category,
                }
                for r in ranked
            ],
        }
    )
    return 0


def _compile_fitness(expression: str) -> Callable[[float], float]:
    """Compile a fitness expression into a callable ``f(x) -> float``."""
    try:
        code = compile(expression, "<fitness-fn>", "eval")
    except SyntaxError as exc:
        raise CLIError(f"invalid --fitness-fn expression: {exc}") from exc

    safe_ns: dict[str, Any] = {
        name: getattr(math, name)
        for name in ("sqrt", "log", "exp", "sin", "cos", "tan", "pow", "pi", "e")
    }
    safe_ns["abs"] = abs
    safe_ns["min"] = min
    safe_ns["max"] = max

    def fitness(x: float) -> float:
        try:
            return float(eval(code, {"__builtins__": {}}, {**safe_ns, "x": x}))
        except CLIError:
            raise
        except Exception as exc:
            raise CLIError(f"--fitness-fn evaluation failed: {exc}") from exc

    return fitness


def _cmd_evolve(args: argparse.Namespace) -> int:
    parts = args.gene_range.split(",")
    if len(parts) != 2:
        raise CLIError("--gene-range must be in the form 'low,high'")
    try:
        low, high = float(parts[0]), float(parts[1])
    except ValueError as exc:
        raise CLIError("--gene-range bounds must be numeric") from exc
    if low >= high:
        raise CLIError("--gene-range requires low < high")

    fitness = _compile_fitness(args.fitness_fn)
    if args.seed is not None:
        random.seed(args.seed)

    engine = EvolutionEngine(
        population_size=args.population_size,
        generations=args.generations,
        mutation_rate=args.mutation_rate,
        elitism=args.elitism,
    )
    result = engine.evolve(fitness_fn=fitness, gene_range=(low, high))
    _emit(
        {
            "best_fitness": result.best_fitness,
            "worst_fitness": result.worst_fitness,
            "generation_count": result.generation_count,
            "population_size": result.population_size,
            "diversity": result.diversity,
            "offspring_count": result.offspring_count,
            "converged": result.converged,
        }
    )
    return 0


def _cmd_benchmark(args: argparse.Namespace) -> int:
    result = Benchmark(name=args.name, target=args.target).evaluate(args.actual)
    _emit(
        {
            "name": args.name,
            "target": args.target,
            "actual": args.actual,
            "passed": result.passed,
            "gap": result.gap,
            "suggestion": result.suggestion,
        }
    )
    return 0


def _cmd_config_show(args: argparse.Namespace) -> int:
    config = _load_config(_resolve_config_path(args.config))
    _emit(config)
    return 0


def _cmd_config_set(args: argparse.Namespace) -> int:
    path = _resolve_config_path(args.config)
    config = _load_config(path)
    new_value = _config_set(config, args.key, args.value)
    _save_config(path, config)
    _emit({"key": args.key, "value": new_value, "config_path": str(path)})
    return 0


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Construct the full argparse parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Acquisition Platform — matching, valuation, fraud, pricing, "
        "portfolio optimization, entity resolution, ranking, and evolution.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to the config JSON file (default: $ACQ_CONFIG or ~/.acq/config.json).",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # match
    p = sub.add_parser("match", help="Match buyers to sellers (GAP solver).")
    p.add_argument("--buyers-file", required=True, help="JSON file with a list of buyers.")
    p.add_argument("--sellers-file", required=True, help="JSON file with a list of sellers.")
    p.set_defaults(func=_cmd_match)

    # value
    p = sub.add_parser("value", help="Value a target (DCF, comps, or ensemble).")
    p.add_argument("--fcf", type=float, default=None, help="Base-year free cash flow.")
    p.add_argument("--revenue", type=float, default=None, help="Annual revenue (comps).")
    p.add_argument("--growth", type=float, default=None, help="FCF growth rate.")
    p.add_argument("--discount", type=float, default=None, help="Discount rate (WACC).")
    p.add_argument(
        "--terminal-growth", type=float, default=None, help="Perpetual growth rate."
    )
    p.add_argument("--multiple", type=float, default=None, help="EV/Revenue multiple.")
    p.add_argument("--years", type=int, default=None, help="Forecast period in years.")
    p.set_defaults(func=_cmd_value)

    # fraud-check
    p = sub.add_parser("fraud-check", help="Score fraud risk from signals.")
    p.add_argument(
        "--signals",
        required=True,
        help="JSON array of [name, value] pairs, {name, value} objects, or an object.",
    )
    p.set_defaults(func=_cmd_fraud_check)

    # optimize
    p = sub.add_parser("optimize", help="Optimize an acquisition portfolio (MIQP).")
    p.add_argument("--budget", type=float, required=True, help="Total capital available.")
    p.add_argument("--max-assets", type=int, default=10, help="Cardinality constraint.")
    p.add_argument("--assets-file", required=True, help="JSON file with a list of assets.")
    p.add_argument(
        "--risk-tolerance", type=float, default=0.5, help="Risk tolerance in [0, 1]."
    )
    p.set_defaults(func=_cmd_optimize)

    # price
    p = sub.add_parser("price", help="Recommend an acquisition price (Stackelberg).")
    p.add_argument("--base-value", type=float, required=True, help="Intrinsic value.")
    p.add_argument("--demand", type=float, required=True, help="Demand level in [0, 1].")
    p.add_argument(
        "--competition", type=float, required=True, help="Competition level in [0, 1]."
    )
    p.add_argument(
        "--market", required=True, help="Market condition: bull, bear, or normal."
    )
    p.set_defaults(func=_cmd_price)

    # resolve
    p = sub.add_parser("resolve", help="Resolve entities into clusters.")
    p.add_argument("--entities-file", required=True, help="JSON file with a list of entities.")
    p.add_argument("--threshold", type=float, default=0.85, help="Similarity threshold.")
    p.set_defaults(func=_cmd_resolve)

    # rank
    p = sub.add_parser("rank", help="Rank listings by relevance and diversity.")
    p.add_argument("--query", required=True, help="Search query string.")
    p.add_argument("--listings-file", required=True, help="JSON file with a list of listings.")
    p.add_argument("--category", default=None, help="Preferred category (personalization).")
    p.set_defaults(func=_cmd_rank)

    # evolve
    p = sub.add_parser("evolve", help="Evolve hyperparameters with a genetic algorithm.")
    p.add_argument(
        "--fitness-fn",
        required=True,
        help="Fitness expression in 'x' (e.g. '-(x-3)**2 + 9').",
    )
    p.add_argument("--gene-range", required=True, help="Search space 'low,high'.")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility.")
    p.add_argument("--population-size", type=int, default=50, help="Population size.")
    p.add_argument("--generations", type=int, default=20, help="Max generations.")
    p.add_argument("--mutation-rate", type=float, default=0.1, help="Per-gene mutation rate.")
    p.add_argument("--elitism", type=int, default=2, help="Elites preserved per generation.")
    p.set_defaults(func=_cmd_evolve)

    # benchmark
    p = sub.add_parser("benchmark", help="Evaluate a metric against a target.")
    p.add_argument("--name", required=True, help="Benchmark name.")
    p.add_argument("--target", type=float, required=True, help="Target value.")
    p.add_argument("--actual", type=float, required=True, help="Actual value.")
    p.set_defaults(func=_cmd_benchmark)

    # config
    p = sub.add_parser("config", help="Show or set configuration values.")
    config_sub = p.add_subparsers(dest="config_command", metavar="ACTION")
    config_sub.required = True
    show = config_sub.add_parser("show", help="Show the effective configuration.")
    show.set_defaults(func=_cmd_config_show)
    setp = config_sub.add_parser("set", help="Set a configuration value.")
    setp.add_argument("key", help="Dotted config key (e.g. entity_resolution.threshold).")
    setp.add_argument("value", help="New value (parsed as JSON when possible).")
    setp.set_defaults(func=_cmd_config_set)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns the process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except CLIError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (KeyError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
