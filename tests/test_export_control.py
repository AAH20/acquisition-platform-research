"""Tests for export control compliance module."""
import pytest

from acquisition_platform.export_control import (
    ExportControlItem,
    ComplianceResult,
    ExportControlAssessor,
)


class TestExportControlAssessor:
    """TDD tests for the export control compliance assessor."""

    def test_itar_classification(self):
        """ITAR technology should be correctly classified."""
        assessor = ExportControlAssessor()
        item = assessor.assess(
            technology_id="TECH-001",
            name="Military Radar System",
            category="defense",
            itar=True,
            ear=False,
            dual_use=False,
        )
        assert item.technology_id == "TECH-001"
        assert item.name == "Military Radar System"
        assert item.category == "defense"
        assert item.itar is True
        assert item.ear is False
        assert item.dual_use is False

    def test_ear_classification(self):
        """EAR technology should be correctly classified."""
        assessor = ExportControlAssessor()
        item = assessor.assess(
            technology_id="TECH-002",
            name="Commercial Encryption",
            category="telecommunications",
            itar=False,
            ear=True,
            dual_use=False,
        )
        assert item.technology_id == "TECH-002"
        assert item.name == "Commercial Encryption"
        assert item.category == "telecommunications"
        assert item.itar is False
        assert item.ear is True
        assert item.dual_use is False

    def test_dual_use_technology(self):
        """Dual-use technology should be flagged."""
        assessor = ExportControlAssessor()
        item = assessor.assess(
            technology_id="TECH-003",
            name="Advanced Semiconductor",
            category="electronics",
            itar=False,
            ear=True,
            dual_use=True,
        )
        assert item.dual_use is True
        assert item.ear is True

    def test_unclassified(self):
        """Unclassified technology should be handled."""
        assessor = ExportControlAssessor()
        item = assessor.assess(
            technology_id="TECH-004",
            name="Basic Software Library",
            category="software",
            itar=False,
            ear=False,
            dual_use=False,
        )
        assert item.itar is False
        assert item.ear is False
        assert item.dual_use is False

    def test_compliance_score(self):
        """Compliance score should be calculated correctly."""
        assessor = ExportControlAssessor()
        items = [
            assessor.assess("T1", "Clean Tech A", "software", False, False, False),
            assessor.assess("T2", "Clean Tech B", "software", False, False, False),
        ]
        score = assessor.compliance_score(items)
        assert score == 1.0

        items_with_risk = [
            assessor.assess("T1", "Clean Tech", "software", False, False, False),
            assessor.assess("T2", "Military Tech", "defense", True, False, False),
        ]
        score = assessor.compliance_score(items_with_risk)
        assert 0.0 < score < 1.0

    def test_empty_portfolio(self):
        """Empty portfolio should return score 0."""
        assessor = ExportControlAssessor()
        score = assessor.compliance_score([])
        assert score == 0.0

    def test_mixed_portfolio(self):
        """Mixed compliance levels should be scored correctly."""
        assessor = ExportControlAssessor()
        items = [
            assessor.assess("T1", "Clean", "software", False, False, False),
            assessor.assess("T2", "EAR Item", "telecom", False, True, False),
            assessor.assess("T3", "Dual Use", "electronics", False, True, True),
            assessor.assess("T4", "ITAR Item", "defense", True, False, False),
        ]
        score = assessor.compliance_score(items)
        assert 0.0 < score < 1.0
        # More clean items = higher score
        clean_items = [
            assessor.assess("T1", "Clean A", "software", False, False, False),
            assessor.assess("T2", "Clean B", "software", False, False, False),
            assessor.assess("T3", "Clean C", "software", False, False, False),
        ]
        clean_score = assessor.compliance_score(clean_items)
        assert clean_score > score

    def test_cross_border_risk(self):
        """Cross-border deal risk should be assessed."""
        assessor = ExportControlAssessor()
        items = [
            assessor.assess("T1", "Military Radar", "defense", True, False, False),
            assessor.assess("T2", "Clean Software", "software", False, False, False),
        ]
        risk = assessor.cross_border_risk(items, "CN")
        assert risk > 0.0
        assert risk <= 1.0

        # Higher risk items should produce higher cross-border risk
        high_risk_items = [
            assessor.assess("T1", "Military Radar", "defense", True, False, False),
            assessor.assess("T2", "Military Engine", "defense", True, False, False),
        ]
        high_risk = assessor.cross_border_risk(high_risk_items, "CN")
        assert high_risk > risk

    def test_iten_exemption(self):
        """ITEN exemption should be checked correctly."""
        assessor = ExportControlAssessor()
        # ITAR items are not eligible for ITEN exemption
        itar_items = [
            assessor.assess("T1", "Military Radar", "defense", True, False, False),
        ]
        assert assessor.iten_exemption(itar_items) is False

        # EAR-only items may be eligible
        ear_items = [
            assessor.assess("T1", "Commercial Encryption", "telecom", False, True, False),
        ]
        assert assessor.iten_exemption(ear_items) is True

        # Clean items are eligible
        clean_items = [
            assessor.assess("T1", "Clean Software", "software", False, False, False),
        ]
        assert assessor.iten_exemption(clean_items) is True

    def test_compliance_report(self):
        """Report should be generated correctly."""
        assessor = ExportControlAssessor()
        items = [
            assessor.assess("T1", "Clean Software", "software", False, False, False),
            assessor.assess("T2", "EAR Item", "telecom", False, True, False),
            assessor.assess("T3", "ITAR Item", "defense", True, False, False),
        ]
        report = assessor.generate_report(items)
        assert isinstance(report, ComplianceResult)
        assert len(report.items) == 3
        assert 0.0 <= report.compliance_score <= 1.0
        assert report.risk_level in ("low", "medium", "high", "critical")
        assert isinstance(report.recommendations, list)
        assert len(report.recommendations) > 0
