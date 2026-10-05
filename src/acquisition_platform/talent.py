"""Talent Assessment Module — team evaluation for M&A due diligence.

Assesses acquisition target teams across multiple dimensions:
clearance levels, tenure, key-person risk, culture fit, and succession
planning. Scores are normalized to [0, 1] where higher is better
(except risk metrics, where higher is worse).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from acquisition_platform.exceptions import ValidationError
from acquisition_platform.serialization import SerializableMixin

# Clearance levels ordered by increasing sensitivity
CLEARANCE_LEVELS: dict[str, float] = {
    "none": 0.0,
    "confidential": 0.1,
    "secret": 0.2,
    "top_secret": 0.3,
    "ts_sci": 0.4,
}

# Tenure (years) at which a member is considered fully stable
FULL_TENURE_YEARS = 10.0

# Valuation multiplier applied to key persons
KEY_PERSON_MULTIPLIER = 2.5

# Weight of key-person concentration in retention risk
KEY_PERSON_RISK_WEIGHT = 0.2


@dataclass
class TeamMember(SerializableMixin):
    """A single team member being assessed.

    Attributes:
        member_id: Unique identifier for the member.
        name: Member's name.
        role: Job role/title.
        clearance: Security clearance level (none, confidential, secret,
            top_secret, ts_sci).
        tenure: Years with the company.
        key_person: Whether this person is critical to operations.
    """

    member_id: str
    name: str
    role: str
    clearance: str
    tenure: float
    key_person: bool


@dataclass
class TeamAssessment(SerializableMixin):
    """Aggregated assessment of a team.

    Attributes:
        members: The team members assessed.
        composition_score: Team quality score in [0, 1] (higher is better).
        retention_risk: Risk of losing staff in [0, 1] (higher is worse).
        stability_score: Team stability in [0, 1] (higher is better).
    """

    members: list[TeamMember] = field(default_factory=list)
    composition_score: float = 0.0
    retention_risk: float = 0.0
    stability_score: float = 0.0


class TalentAssessor:
    """Assesses talent teams for acquisition due diligence.

    Provides methods to evaluate individual members, team composition,
    retention risk, stability, culture fit, and succession risk.
    """

    def assess(
        self,
        member_id: str,
        name: str,
        role: str,
        clearance: str,
        tenure: float,
        key_person: bool,
    ) -> TeamMember:
        """Create a validated TeamMember.

        Args:
            member_id: Unique identifier for the member.
            name: Member's name.
            role: Job role/title.
            clearance: Security clearance level.
            tenure: Years with the company (must be non-negative).
            key_person: Whether this person is critical to operations.

        Returns:
            A validated TeamMember instance.

        Raises:
            ValidationError: If clearance is unknown or tenure is negative.
        """
        if clearance not in CLEARANCE_LEVELS:
            raise ValidationError(
                f"Unknown clearance level: {clearance!r}. "
                f"Valid levels: {sorted(CLEARANCE_LEVELS)}"
            )
        if tenure < 0:
            raise ValidationError(f"tenure must be non-negative, got {tenure}")
        return TeamMember(
            member_id=member_id,
            name=name,
            role=role,
            clearance=clearance,
            tenure=tenure,
            key_person=key_person,
        )

    def key_person_valuation(self, member: TeamMember, salary: float) -> float:
        """Compute the valuation of a key person.

        Valuation = salary * (1 + clearance_premium) * key_person_multiplier.
        Non-key persons receive no multiplier.

        Args:
            member: The team member to value.
            salary: Annual salary (must be non-negative).

        Returns:
            The computed valuation.

        Raises:
            ValidationError: If salary is negative.
        """
        if salary < 0:
            raise ValidationError(f"salary must be non-negative, got {salary}")
        premium = self.clearance_premium(member.clearance)
        multiplier = KEY_PERSON_MULTIPLIER if member.key_person else 1.0
        return salary * (1 + premium) * multiplier

    def clearance_premium(self, clearance: str) -> float:
        """Return the salary premium for a clearance level.

        Args:
            clearance: Security clearance level.

        Returns:
            Premium in [0.0, 0.4].

        Raises:
            ValidationError: If clearance level is unknown.
        """
        if clearance not in CLEARANCE_LEVELS:
            raise ValidationError(
                f"Unknown clearance level: {clearance!r}. "
                f"Valid levels: {sorted(CLEARANCE_LEVELS)}"
            )
        return CLEARANCE_LEVELS[clearance]

    def team_composition_score(self, members: list[TeamMember]) -> float:
        """Score team composition based on clearance and tenure.

        Per-member score = 0.5 * (clearance_premium / 0.4)
                        + 0.5 * min(tenure / 10, 1.0).
        Team score is the average across members.

        Args:
            members: Team members to score.

        Returns:
            Composition score in [0, 1], or 0.0 for an empty team.
        """
        if not members:
            return 0.0
        total = 0.0
        for m in members:
            clearance_component = self.clearance_premium(m.clearance) / 0.4
            tenure_component = min(m.tenure / FULL_TENURE_YEARS, 1.0)
            total += 0.5 * clearance_component + 0.5 * tenure_component
        return total / len(members)

    def retention_risk(self, members: list[TeamMember]) -> float:
        """Assess the risk of losing team members.

        Risk increases with shorter average tenure and higher
        key-person concentration.

        Args:
            members: Team members to assess.

        Returns:
            Retention risk in [0, 1], or 0.0 for an empty team.
        """
        if not members:
            return 0.0
        avg_tenure = sum(m.tenure for m in members) / len(members)
        tenure_risk = 1.0 - min(avg_tenure / FULL_TENURE_YEARS, 1.0)
        key_ratio = sum(1 for m in members if m.key_person) / len(members)
        risk = tenure_risk + KEY_PERSON_RISK_WEIGHT * key_ratio
        return min(risk, 1.0)

    def stability_score(self, members: list[TeamMember]) -> float:
        """Score team stability (inverse of retention risk).

        Args:
            members: Team members to score.

        Returns:
            Stability score in [0, 1], or 0.0 for an empty team.
        """
        if not members:
            return 0.0
        return 1.0 - self.retention_risk(members)

    def culture_fit(
        self, company_culture: dict[str, float], target_culture: dict[str, float]
    ) -> float:
        """Assess cultural compatibility between two organizations.

        Fit = 1 - mean(|company[k] - target[k]|) across all dimensions
        present in either culture profile.

        Args:
            company_culture: Culture profile of the acquiring company.
            target_culture: Culture profile of the acquisition target.

        Returns:
            Culture fit score in [0, 1] (1.0 = identical).
        """
        if not company_culture and not target_culture:
            return 1.0
        all_keys = set(company_culture) | set(target_culture)
        if not all_keys:
            return 1.0
        total_diff = sum(
            abs(company_culture.get(k, 0.0) - target_culture.get(k, 0.0))
            for k in all_keys
        )
        return max(0.0, 1.0 - total_diff / len(all_keys))

    def succession_risk(self, members: list[TeamMember]) -> float:
        """Assess risk from key-person concentration.

        Risk = key_person_ratio * (1 - min(avg_key_tenure / 10, 1.0)).
        Teams with no key persons have zero succession risk.

        Args:
            members: Team members to assess.

        Returns:
            Succession risk in [0, 1], or 0.0 for an empty team.
        """
        if not members:
            return 0.0
        key_members = [m for m in members if m.key_person]
        if not key_members:
            return 0.0
        key_ratio = len(key_members) / len(members)
        avg_key_tenure = sum(m.tenure for m in key_members) / len(key_members)
        tenure_factor = 1.0 - min(avg_key_tenure / FULL_TENURE_YEARS, 1.0)
        return key_ratio * tenure_factor

    def assess_team(self, members: list[TeamMember]) -> TeamAssessment:
        """Perform a full assessment of a team.

        Args:
            members: Team members to assess.

        Returns:
            TeamAssessment with all computed scores.
        """
        return TeamAssessment(
            members=list(members),
            composition_score=self.team_composition_score(members),
            retention_risk=self.retention_risk(members),
            stability_score=self.stability_score(members),
        )
