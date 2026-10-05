"""Compliance Module.

Provides compliance checking, regulatory mapping, scoring, audit trails,
policy enforcement, monitoring, remediation planning, and alerting.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from acquisition_platform.observability import get_logger, log_execution_time

logger = get_logger(__name__)


@dataclass
class ComplianceRule:
    """A compliance rule definition."""

    rule_id: str
    name: str
    regulation: str
    category: str
    severity: str


@dataclass
class ComplianceResult:
    """Result of a compliance check."""

    rules: list[ComplianceRule] = field(default_factory=list)
    score: float = 0.0
    violations: list[str] = field(default_factory=list)
    audit_trail: list[dict[str, Any]] = field(default_factory=list)


class ComplianceManager:
    """Manages compliance checking, monitoring, and reporting."""

    _SEVERITY_ORDER: dict[str, int] = {"low": 0, "medium": 1, "high": 2, "critical": 3}

    @log_execution_time(logger)
    def check_compliance(
        self, rules: list[ComplianceRule], data: dict[str, Any]
    ) -> ComplianceResult:
        """Check compliance of data against a set of rules.

        Args:
            rules: List of compliance rules to check.
            data: Data to evaluate against the rules.

        Returns:
            ComplianceResult with score, violations, and audit trail.
        """
        violations: list[str] = []
        audit_trail: list[dict[str, Any]] = []
        compliant_count = 0

        for rule in rules:
            is_compliant = self._evaluate_rule(rule, data)
            entry = {
                "rule_id": rule.rule_id,
                "rule_name": rule.name,
                "regulation": rule.regulation,
                "category": rule.category,
                "severity": rule.severity,
                "compliant": is_compliant,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            audit_trail.append(entry)

            if is_compliant:
                compliant_count += 1
            else:
                violations.append(
                    f"[{rule.severity.upper()}] {rule.name} ({rule.regulation}): "
                    f"non-compliant in category '{rule.category}'"
                )

        score = compliant_count / len(rules) if rules else 0.0

        return ComplianceResult(
            rules=list(rules),
            score=score,
            violations=violations,
            audit_trail=audit_trail,
        )

    @log_execution_time(logger)
    def map_regulations(
        self, industry: str, jurisdiction: str
    ) -> list[ComplianceRule]:
        """Map regulations to compliance rules for an industry and jurisdiction.

        Args:
            industry: Industry sector (e.g., 'defense', 'healthcare', 'finance').
            jurisdiction: Jurisdiction code (e.g., 'US', 'EU', 'UK').

        Returns:
            List of applicable ComplianceRule objects.
        """
        rules: list[ComplianceRule] = []

        # Base rules applicable to all industries
        rules.append(
            ComplianceRule(
                rule_id="BASE-001",
                name="Data Protection",
                regulation="GDPR" if jurisdiction.upper() == "EU" else "CCPA",
                category="privacy",
                severity="high",
            )
        )

        # Industry-specific rules
        industry_rules = self._get_industry_rules(industry, jurisdiction)
        rules.extend(industry_rules)

        return rules

    @log_execution_time(logger)
    def calculate_compliance_score(self, results: list[ComplianceResult]) -> float:
        """Calculate aggregate compliance score from multiple results.

        Args:
            results: List of ComplianceResult objects.

        Returns:
            Average compliance score in [0, 1].
        """
        if not results:
            return 0.0
        return sum(r.score for r in results) / len(results)

    @log_execution_time(logger)
    def generate_audit_trail(self, actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate an audit trail from a list of actions.

        Args:
            actions: List of action dict[str, Any]ionaries.

        Returns:
            List of audit trail entries with timestamps.
        """
        trail: list[dict[str, Any]] = []
        for action in actions:
            entry = dict[str, Any](action)
            entry.setdefault(
                "timestamp", datetime.now(timezone.utc).isoformat()
            )
            trail.append(entry)
        return trail

    @log_execution_time(logger)
    def enforce_policy(self, rule: ComplianceRule, data: dict[str, Any]) -> bool:
        """Enforce a compliance policy against data.

        Args:
            rule: The compliance rule to enforce.
            data: Data to check.

        Returns:
            True if the data complies with the rule, False otherwise.
        """
        return self._evaluate_rule(rule, data)

    @log_execution_time(logger)
    def monitor_compliance(self, rules: list[ComplianceRule]) -> dict[str, Any]:
        """Monitor compliance status across a set of rules.

        Args:
            rules: List of compliance rules to monitor.

        Returns:
            Monitoring status dict[str, Any]ionary.
        """
        severity_counts: dict[str, int] = {}
        for rule in rules:
            severity_counts[rule.severity] = severity_counts.get(rule.severity, 0) + 1

        return {
            "total_rules": len(rules),
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "name": r.name,
                    "regulation": r.regulation,
                    "category": r.category,
                    "severity": r.severity,
                }
                for r in rules
            ],
            "severity_breakdown": severity_counts,
            "status": "active",
        }

    @log_execution_time(logger)
    def generate_remediation_plan(self, violations: list[str]) -> list[str]:
        """Generate a remediation plan from violations.

        Args:
            violations: List of violation descriptions.

        Returns:
            List of remediation steps.
        """
        plan: list[str] = []
        for i, violation in enumerate(violations, start=1):
            plan.append(
                f"Step {i}: Remediate violation - {violation}. "
                "Implement corrective controls and verify compliance."
            )
        return plan

    @log_execution_time(logger)
    def generate_compliance_alerts(self, violations: list[str]) -> list[str]:
        """Generate alerts from violations.

        Args:
            violations: List of violation descriptions.

        Returns:
            List of alert messages.
        """
        alerts: list[str] = []
        for violation in violations:
            alerts.append(
                f"ALERT: Compliance violation detected - {violation}. "
                "Immediate attention required."
            )
        return alerts

    @log_execution_time(logger)
    def generate_compliance_report(self, results: list[ComplianceResult]) -> dict[str, Any]:
        """Generate a compliance report from results.

        Args:
            results: List of ComplianceResult objects.

        Returns:
            Report dict[str, Any]ionary with score, violations, and rules checked.
        """
        all_violations: list[str] = []
        total_rules = 0
        for result in results:
            all_violations.extend(result.violations)
            total_rules += len(result.rules)

        score = self.calculate_compliance_score(results)

        return {
            "score": score,
            "violations": all_violations,
            "rules_checked": total_rules,
            "violation_count": len(all_violations),
            "compliant": len(all_violations) == 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _evaluate_rule(self, rule: ComplianceRule, data: dict[str, Any]) -> bool:
        """Evaluate a single rule against data.

        A rule is compliant if the data contains a truthy value for the
        rule's category key (e.g., 'privacy' -> data['privacy'] is True).

        Args:
            rule: The compliance rule.
            data: The data to evaluate.

        Returns:
            True if compliant, False otherwise.
        """
        # Check for category-specific compliance key
        category_key = rule.category.lower()
        if category_key in data:
            return bool(data[category_key])

        # Check for has_<category> pattern
        has_key = f"has_{category_key}"
        if has_key in data:
            return bool(data[has_key])

        # Check for has_<category>_policy pattern
        has_policy_key = f"has_{category_key}_policy"
        if has_policy_key in data:
            return bool(data[has_policy_key])

        # Check for rule_id-based key
        rule_key = rule.rule_id.lower()
        if rule_key in data:
            return bool(data[rule_key])

        # Default: non-compliant if no matching key found
        return False

    def _get_industry_rules(
        self, industry: str, jurisdiction: str
    ) -> list[ComplianceRule]:
        """Get industry-specific compliance rules.

        Args:
            industry: Industry sector.
            jurisdiction: Jurisdiction code.

        Returns:
            List of industry-specific ComplianceRule objects.
        """
        rules: list[ComplianceRule] = []
        ind = industry.lower()
        jur = jurisdiction.upper()

        if ind == "defense":
            rules.append(
                ComplianceRule(
                    rule_id="DEF-001",
                    name="ITAR Compliance",
                    regulation="ITAR",
                    category="export",
                    severity="critical",
                )
            )
            rules.append(
                ComplianceRule(
                    rule_id="DEF-002",
                    name="Export Control",
                    regulation="EAR",
                    category="export",
                    severity="high",
                )
            )
        elif ind == "healthcare":
            rules.append(
                ComplianceRule(
                    rule_id="HC-001",
                    name="HIPAA Compliance",
                    regulation="HIPAA",
                    category="privacy",
                    severity="critical",
                )
            )
        elif ind == "finance":
            rules.append(
                ComplianceRule(
                    rule_id="FIN-001",
                    name="SOX Compliance",
                    regulation="SOX",
                    category="financial",
                    severity="high",
                )
            )
            rules.append(
                ComplianceRule(
                    rule_id="FIN-002",
                    name="AML Compliance",
                    regulation="AML",
                    category="financial",
                    severity="critical",
                )
            )

        # Jurisdiction-specific additions
        if jur == "EU":
            rules.append(
                ComplianceRule(
                    rule_id="EU-001",
                    name="GDPR Data Rights",
                    regulation="GDPR",
                    category="privacy",
                    severity="high",
                )
            )
        elif jur == "US":
            rules.append(
                ComplianceRule(
                    rule_id="US-001",
                    name="CCPA Compliance",
                    regulation="CCPA",
                    category="privacy",
                    severity="medium",
                )
            )

        return rules
