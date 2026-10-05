"""Tests for talent assessment module."""
import pytest

from acquisition_platform.talent import (
    TalentAssessor,
    TeamAssessment,
    TeamMember,
)


class TestTalentAssessor:
    """TDD tests for the talent assessment module."""

    def test_key_person_valuation(self):
        assessor = TalentAssessor()
        key_person = assessor.assess("M1", "Alice", "Engineer", "secret", 5.0, True)
        valuation = assessor.key_person_valuation(key_person, 100000)
        # salary * (1 + premium) * key_person_multiplier
        # 100000 * 1.2 * 2.5 = 300000
        assert valuation == 300000.0

    def test_clearance_premium(self):
        assessor = TalentAssessor()
        assert assessor.clearance_premium("none") == 0.0
        assert assessor.clearance_premium("confidential") == 0.1
        assert assessor.clearance_premium("secret") == 0.2
        assert assessor.clearance_premium("top_secret") == 0.3
        assert assessor.clearance_premium("ts_sci") == 0.4
        # All premiums within [0.0, 0.4]
        for level in ["none", "confidential", "secret", "top_secret", "ts_sci"]:
            premium = assessor.clearance_premium(level)
            assert 0.0 <= premium <= 0.4

    def test_team_composition_score(self):
        assessor = TalentAssessor()
        member = assessor.assess("M1", "Alice", "Engineer", "top_secret", 10.0, False)
        # clearance component: 0.3/0.4 = 0.75, tenure component: min(10/10, 1) = 1.0
        # score = 0.5 * 0.75 + 0.5 * 1.0 = 0.875
        score = assessor.team_composition_score([member])
        assert score == pytest.approx(0.875)

    def test_retention_risk(self):
        assessor = TalentAssessor()
        short_tenure = [
            assessor.assess("M1", "Alice", "Engineer", "secret", 1.0, False),
            assessor.assess("M2", "Bob", "Manager", "secret", 1.0, False),
        ]
        long_tenure = [
            assessor.assess("M3", "Carol", "Engineer", "secret", 10.0, False),
            assessor.assess("M4", "Dave", "Manager", "secret", 10.0, False),
        ]
        short_risk = assessor.retention_risk(short_tenure)
        long_risk = assessor.retention_risk(long_tenure)
        assert short_risk > long_risk
        assert 0.0 <= short_risk <= 1.0
        assert 0.0 <= long_risk <= 1.0

    def test_empty_team(self):
        assessor = TalentAssessor()
        assert assessor.team_composition_score([]) == 0.0
        assert assessor.retention_risk([]) == 0.0
        assert assessor.stability_score([]) == 0.0
        assert assessor.succession_risk([]) == 0.0

    def test_mixed_clearances(self):
        assessor = TalentAssessor()
        low_team = [
            assessor.assess("M1", "Alice", "Engineer", "none", 5.0, False),
            assessor.assess("M2", "Bob", "Manager", "none", 5.0, False),
        ]
        high_team = [
            assessor.assess("M3", "Carol", "Engineer", "ts_sci", 5.0, False),
            assessor.assess("M4", "Dave", "Manager", "ts_sci", 5.0, False),
        ]
        low_score = assessor.team_composition_score(low_team)
        high_score = assessor.team_composition_score(high_team)
        assert high_score > low_score

    def test_team_stability(self):
        assessor = TalentAssessor()
        short_tenure = [
            assessor.assess("M1", "Alice", "Engineer", "secret", 1.0, False),
        ]
        long_tenure = [
            assessor.assess("M2", "Bob", "Engineer", "secret", 10.0, False),
        ]
        short_stability = assessor.stability_score(short_tenure)
        long_stability = assessor.stability_score(long_tenure)
        assert long_stability > short_stability
        assert 0.0 <= short_stability <= 1.0
        assert 0.0 <= long_stability <= 1.0

    def test_culture_fit(self):
        assessor = TalentAssessor()
        company = {"innovation": 0.8, "stability": 0.5, "customer_focus": 0.9}
        target = {"innovation": 0.8, "stability": 0.5, "customer_focus": 0.9}
        # Identical cultures -> perfect fit
        assert assessor.culture_fit(company, target) == pytest.approx(1.0)
        # Completely different
        opposite = {"innovation": 0.0, "stability": 1.0, "customer_focus": 0.0}
        fit = assessor.culture_fit(company, opposite)
        assert fit < 0.5
        assert 0.0 <= fit <= 1.0

    def test_talent_portfolio(self):
        assessor = TalentAssessor()
        teams = [
            [
                assessor.assess("M1", "Alice", "CTO", "ts_sci", 8.0, True),
                assessor.assess("M2", "Bob", "Engineer", "secret", 5.0, False),
            ],
            [
                assessor.assess("M3", "Carol", "CEO", "top_secret", 12.0, True),
                assessor.assess("M4", "Dave", "CFO", "secret", 10.0, True),
                assessor.assess("M5", "Eve", "Engineer", "confidential", 3.0, False),
            ],
        ]
        assessments = [assessor.assess_team(team) for team in teams]
        assert len(assessments) == 2
        for assessment in assessments:
            assert isinstance(assessment, TeamAssessment)
            assert len(assessment.members) > 0
            assert 0.0 <= assessment.composition_score <= 1.0
            assert 0.0 <= assessment.retention_risk <= 1.0
            assert 0.0 <= assessment.stability_score <= 1.0

    def test_succession_risk(self):
        assessor = TalentAssessor()
        # Single key person with short tenure -> high succession risk
        concentrated = [
            assessor.assess("M1", "Alice", "CTO", "ts_sci", 2.0, True),
            assessor.assess("M2", "Bob", "Engineer", "secret", 5.0, False),
        ]
        # Multiple key persons with long tenure -> lower succession risk
        distributed = [
            assessor.assess("M3", "Carol", "CEO", "top_secret", 10.0, True),
            assessor.assess("M4", "Dave", "CFO", "secret", 10.0, True),
            assessor.assess("M5", "Eve", "Engineer", "confidential", 8.0, False),
        ]
        concentrated_risk = assessor.succession_risk(concentrated)
        distributed_risk = assessor.succession_risk(distributed)
        assert concentrated_risk > distributed_risk
        assert 0.0 <= concentrated_risk <= 1.0
        assert 0.0 <= distributed_risk <= 1.0
