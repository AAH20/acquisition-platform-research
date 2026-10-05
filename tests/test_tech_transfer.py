"""Tests for technology transfer module."""
import pytest
from acquisition_platform.tech_transfer import (
    TransferProfile,
    TransferResult,
    TechTransferAnalyzer,
)
from acquisition_platform.exceptions import ValidationError


class TestTransferProfile:
    """Tests for TransferProfile dataclass."""

    def test_profile_creation(self):
        """TransferProfile can be created with all fields."""
        profile = TransferProfile(
            technology_id="tech-001",
            name="Quantum Sensor",
            trl=6,
            source_type="university",
            target_type="corporate",
            complexity=0.4,
        )
        assert profile.technology_id == "tech-001"
        assert profile.name == "Quantum Sensor"
        assert profile.trl == 6
        assert profile.source_type == "university"
        assert profile.target_type == "corporate"
        assert profile.complexity == 0.4


class TestTransferResult:
    """Tests for TransferResult dataclass."""

    def test_result_creation(self):
        """TransferResult can be created with all fields."""
        profile = TransferProfile(
            technology_id="tech-001",
            name="Quantum Sensor",
            trl=6,
            source_type="university",
            target_type="corporate",
            complexity=0.4,
        )
        result = TransferResult(
            profile=profile,
            readiness_score=0.75,
            absorptive_capacity=0.6,
            risk_level="medium",
            timeline_months=12,
        )
        assert result.profile is profile
        assert result.readiness_score == 0.75
        assert result.absorptive_capacity == 0.6
        assert result.risk_level == "medium"
        assert result.timeline_months == 12


class TestTechTransferAnalyzer:
    """TDD tests for TechTransferAnalyzer."""

    def test_transfer_readiness(self):
        """Transfer readiness scored based on TRL and complexity."""
        analyzer = TechTransferAnalyzer()
        profile = TransferProfile(
            technology_id="tech-001",
            name="Quantum Sensor",
            trl=8,
            source_type="university",
            target_type="corporate",
            complexity=0.2,
        )
        score = analyzer.assess_transfer_readiness(profile)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # High TRL + low complexity = high readiness
        assert score > 0.7

    def test_absorptive_capacity(self):
        """Absorptive capacity assessed based on capability gap."""
        analyzer = TechTransferAnalyzer()
        # Target capability >= source capability = full absorption
        high = analyzer.absorptive_capacity(target_capability=0.8, source_capability=0.5)
        assert high == pytest.approx(1.0)
        # Target capability < source capability = partial absorption
        low = analyzer.absorptive_capacity(target_capability=0.3, source_capability=0.9)
        assert 0.0 <= low < 1.0
        # Equal capabilities = full absorption
        equal = analyzer.absorptive_capacity(target_capability=0.5, source_capability=0.5)
        assert equal == pytest.approx(1.0)

    def test_empty_transfer(self):
        """Empty transfer returns defaults."""
        analyzer = TechTransferAnalyzer()
        # Empty knowledge lists = perfect transfer score
        score = analyzer.knowledge_transfer_score([], [])
        assert score == pytest.approx(1.0)
        # Empty spinoff dict = zero score
        spinoff_score = analyzer.university_spinoff_score({})
        assert spinoff_score == pytest.approx(0.0)
        # Empty TTO dict = zero score
        tto_score = analyzer.tto_assessment({})
        assert tto_score == pytest.approx(0.0)

    def test_university_spinoff(self):
        """University spinoff scored correctly."""
        analyzer = TechTransferAnalyzer()
        spinoff = {
            "trl": 7,
            "patents": 5,
            "funding": 500_000,
            "team_size": 8,
        }
        score = analyzer.university_spinoff_score(spinoff)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # Strong spinoff should score well
        assert score > 0.5

    def test_license_valuation(self):
        """License valued correctly."""
        analyzer = TechTransferAnalyzer()
        # value = revenue * royalty_rate * duration
        value = analyzer.value_license(
            revenue=1_000_000, royalty_rate=0.05, duration=10
        )
        assert value == pytest.approx(500_000.0)
        # Zero revenue = zero value
        zero = analyzer.value_license(revenue=0, royalty_rate=0.1, duration=5)
        assert zero == pytest.approx(0.0)

    def test_transfer_risk(self):
        """Transfer risk assessed based on TRL and complexity."""
        analyzer = TechTransferAnalyzer()
        # Low TRL + high complexity = high risk
        risky_profile = TransferProfile(
            technology_id="tech-002",
            name="Risky Tech",
            trl=2,
            source_type="university",
            target_type="corporate",
            complexity=0.9,
        )
        risk = analyzer.transfer_risk(risky_profile)
        assert isinstance(risk, float)
        assert 0.0 <= risk <= 1.0
        assert risk > 0.5

    def test_knowledge_transfer(self):
        """Knowledge transfer scored based on overlap."""
        analyzer = TechTransferAnalyzer()
        # High overlap = high transfer score
        source = ["AI", "ML", "robotics", "sensors"]
        target = ["AI", "ML", "robotics", "manufacturing"]
        score = analyzer.knowledge_transfer_score(source, target)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # 3 out of 5 unique areas overlap
        assert score == pytest.approx(0.6)

    def test_transfer_report(self):
        """Report generated with all fields."""
        analyzer = TechTransferAnalyzer()
        profile = TransferProfile(
            technology_id="tech-003",
            name="AI Chip",
            trl=7,
            source_type="corporate",
            target_type="corporate",
            complexity=0.3,
        )
        result = analyzer.generate_transfer_report(profile)
        assert isinstance(result, TransferResult)
        assert result.profile is profile
        assert isinstance(result.readiness_score, float)
        assert isinstance(result.absorptive_capacity, float)
        assert result.risk_level in ("low", "medium", "high")
        assert isinstance(result.timeline_months, int)
        assert result.timeline_months > 0

    def test_tto_assessment(self):
        """TTO assessment scored correctly."""
        analyzer = TechTransferAnalyzer()
        tto = {
            "staff_count": 15,
            "patents_licensed": 30,
            "startups_created": 5,
            "revenue_generated": 5_000_000,
        }
        score = analyzer.tto_assessment(tto)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # Strong TTO should score well
        assert score > 0.5

    def test_transfer_timeline(self):
        """Timeline generated based on TRL and complexity."""
        analyzer = TechTransferAnalyzer()
        # Low TRL + high complexity = long timeline
        complex_profile = TransferProfile(
            technology_id="tech-004",
            name="Complex Tech",
            trl=3,
            source_type="university",
            target_type="corporate",
            complexity=0.8,
        )
        timeline = analyzer.transfer_timeline(complex_profile)
        assert isinstance(timeline, int)
        assert timeline > 0
        # High TRL + low complexity = short timeline
        simple_profile = TransferProfile(
            technology_id="tech-005",
            name="Simple Tech",
            trl=8,
            source_type="corporate",
            target_type="corporate",
            complexity=0.1,
        )
        short_timeline = analyzer.transfer_timeline(simple_profile)
        assert short_timeline < timeline
