"""Tests for compliance module."""
import pytest

from acquisition_platform.compliance import (
    ComplianceRule,
    ComplianceResult,
    ComplianceManager,
)


class TestComplianceManager:
    """TDD tests for the compliance manager."""

    def test_compliance_check(self):
        """Compliance should be checked against rules and data."""
        manager = ComplianceManager()
        rules = [
            ComplianceRule("R1", "Data Privacy", "GDPR", "privacy", "high"),
            ComplianceRule("R2", "Export Control", "ITAR", "export", "critical"),
        ]
        data = {"has_privacy_policy": True, "has_export_license": False}
        result = manager.check_compliance(rules, data)
        assert isinstance(result, ComplianceResult)
        assert result.rules == rules
        assert isinstance(result.score, float)
        assert isinstance(result.violations, list)
        assert isinstance(result.audit_trail, list)

    def test_regulatory_mapping(self):
        """Regulations should be mapped for industry and jurisdiction."""
        manager = ComplianceManager()
        rules = manager.map_regulations("defense", "US")
        assert isinstance(rules, list)
        assert len(rules) > 0
        assert all(isinstance(r, ComplianceRule) for r in rules)
        assert all(r.regulation for r in rules)

    def test_empty_compliance(self):
        """Empty rules should return defaults."""
        manager = ComplianceManager()
        result = manager.check_compliance([], {})
        assert isinstance(result, ComplianceResult)
        assert result.rules == []
        assert result.score == 0.0
        assert result.violations == []
        assert isinstance(result.audit_trail, list)

    def test_compliance_score(self):
        """Compliance score should be calculated from results."""
        manager = ComplianceManager()
        rules = [
            ComplianceRule("R1", "Rule A", "GDPR", "privacy", "high"),
            ComplianceRule("R2", "Rule B", "SOX", "financial", "medium"),
        ]
        data = {"has_privacy_policy": True, "has_financial_controls": True}
        result = manager.check_compliance(rules, data)
        score = manager.calculate_compliance_score([result])
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_audit_trail(self):
        """Audit trail should be generated from actions."""
        manager = ComplianceManager()
        actions = [
            {"action": "check", "rule_id": "R1", "timestamp": "2024-01-01"},
            {"action": "enforce", "rule_id": "R2", "timestamp": "2024-01-02"},
        ]
        trail = manager.generate_audit_trail(actions)
        assert isinstance(trail, list)
        assert len(trail) == 2
        assert all(isinstance(entry, dict) for entry in trail)
        assert all("action" in entry for entry in trail)

    def test_compliance_report(self):
        """Compliance report should be generated from results."""
        manager = ComplianceManager()
        rules = [ComplianceRule("R1", "Rule A", "GDPR", "privacy", "high")]
        data = {"has_privacy_policy": True}
        result = manager.check_compliance(rules, data)
        report = manager.generate_compliance_report([result])
        assert isinstance(report, dict)
        assert "score" in report
        assert "violations" in report
        assert "rules_checked" in report

    def test_policy_enforcement(self):
        """Policies should be enforced against data."""
        manager = ComplianceManager()
        rule = ComplianceRule("R1", "Data Privacy", "GDPR", "privacy", "high")
        # Compliant data
        assert manager.enforce_policy(rule, {"has_privacy_policy": True}) is True
        # Non-compliant data
        assert manager.enforce_policy(rule, {"has_privacy_policy": False}) is False

    def test_compliance_monitoring(self):
        """Compliance should be monitored across rules."""
        manager = ComplianceManager()
        rules = [
            ComplianceRule("R1", "Rule A", "GDPR", "privacy", "high"),
            ComplianceRule("R2", "Rule B", "SOX", "financial", "medium"),
        ]
        status = manager.monitor_compliance(rules)
        assert isinstance(status, dict)
        assert "total_rules" in status
        assert "rules" in status
        assert status["total_rules"] == 2

    def test_remediation_plan(self):
        """Remediation plan should be generated from violations."""
        manager = ComplianceManager()
        violations = ["Missing privacy policy", "No export license"]
        plan = manager.generate_remediation_plan(violations)
        assert isinstance(plan, list)
        assert len(plan) == 2
        assert all(isinstance(step, str) for step in plan)
        assert all("remediate" in step.lower() or "fix" in step.lower() or "address" in step.lower() for step in plan)

    def test_compliance_alerts(self):
        """Alerts should be generated from violations."""
        manager = ComplianceManager()
        violations = ["Critical: ITAR violation", "High: Missing GDPR consent"]
        alerts = manager.generate_compliance_alerts(violations)
        assert isinstance(alerts, list)
        assert len(alerts) == 2
        assert all(isinstance(alert, str) for alert in alerts)
        assert all("alert" in alert.lower() or "violation" in alert.lower() for alert in alerts)
