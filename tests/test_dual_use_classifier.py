"""Tests for the dual-use technology classifier module (TDD)."""
from acquisition_platform.dual_use_classifier import (
    ClassificationResult,
    DualUseClassifier,
    TechnologyProfile,
)


def _profile(
    name="Advanced Radar",
    category="dual_use",
    military_apps=None,
    commercial_apps=None,
    trl=7,
    export_control="EAR",
):
    """Helper to build a TechnologyProfile with sensible defaults."""
    return TechnologyProfile(
        name=name,
        category=category,
        military_apps=list(military_apps) if military_apps is not None else ["targeting"],
        commercial_apps=list(commercial_apps) if commercial_apps is not None else ["weather"],
        trl=trl,
        export_control=export_control,
    )


class TestDualUseClassifier:
    """TDD tests for the dual-use technology classifier."""

    def test_classify_technology(self):
        """Technology should be classified by dual-use potential."""
        classifier = DualUseClassifier()
        result = classifier.classify(_profile())
        assert isinstance(result, ClassificationResult)
        assert isinstance(result.profile, TechnologyProfile)
        assert result.classification in (
            "high_dual_use",
            "low_dual_use",
            "military_only",
            "commercial_only",
            "neither",
        )
        assert 0.0 <= result.dual_use_score <= 1.0

    def test_military_application(self):
        """Military applications should be detected and scored."""
        classifier = DualUseClassifier()
        military = _profile(
            category="defense",
            military_apps=["missile guidance", "surveillance", "radar"],
            commercial_apps=[],
        )
        score = classifier.military_application_score(military)
        assert score > 0.0
        assert score <= 1.0

        # No military apps -> zero military score
        commercial_only = _profile(military_apps=[], commercial_apps=["mapping"])
        assert classifier.military_application_score(commercial_only) == 0.0

    def test_commercial_application(self):
        """Commercial applications should be detected and scored."""
        classifier = DualUseClassifier()
        commercial = _profile(
            category="commercial",
            military_apps=[],
            commercial_apps=["logistics", "analytics", "mapping"],
        )
        score = classifier.commercial_application_score(commercial)
        assert score > 0.0
        assert score <= 1.0

        # No commercial apps -> zero commercial score
        military_only = _profile(military_apps=["targeting"], commercial_apps=[])
        assert classifier.commercial_application_score(military_only) == 0.0

    def test_dual_use_score(self):
        """Dual-use score should be calculated and bounded in [0, 1]."""
        classifier = DualUseClassifier()
        both = _profile(
            military_apps=["targeting", "surveillance", "radar"],
            commercial_apps=["weather", "mapping", "navigation"],
        )
        score = classifier.dual_use_score(both)
        assert 0.0 <= score <= 1.0

        # Technology present in both domains scores higher than one domain only
        only_one = _profile(military_apps=["targeting"], commercial_apps=[])
        assert score > classifier.dual_use_score(only_one)

    def test_empty_technology(self):
        """Empty input should return safe defaults, not raise."""
        classifier = DualUseClassifier()
        empty = TechnologyProfile(
            name="",
            category="",
            military_apps=[],
            commercial_apps=[],
            trl=1,
            export_control="none",
        )
        assert classifier.military_application_score(empty) == 0.0
        assert classifier.commercial_application_score(empty) == 0.0
        assert classifier.dual_use_score(empty) == 0.0
        assert classifier.classify_category(empty) == "neither"
        assert classifier.regulatory_flags(empty) == []

        result = classifier.classify(empty)
        assert result.classification == "neither"
        assert result.dual_use_score == 0.0
        assert result.regulatory_flags == []

    def test_high_dual_use(self):
        """A mature technology with both strong military and commercial use is high dual-use."""
        classifier = DualUseClassifier()
        high = _profile(
            category="dual_use",
            military_apps=["targeting", "surveillance", "electronic warfare"],
            commercial_apps=["weather", "mapping", "navigation"],
            trl=8,
            export_control="EAR",
        )
        result = classifier.classify(high)
        assert result.dual_use_score >= 0.5
        assert result.classification == "high_dual_use"

    def test_low_dual_use(self):
        """A technology with weak presence in both domains is low dual-use."""
        classifier = DualUseClassifier()
        low = _profile(
            category="dual_use",
            military_apps=["targeting"],
            commercial_apps=["mapping"],
            trl=4,
            export_control="none",
        )
        result = classifier.classify(low)
        assert result.dual_use_score < 0.5
        assert result.classification == "low_dual_use"

    def test_category_classification(self):
        """Category should resolve to military_only/commercial_only/dual_use/neither."""
        classifier = DualUseClassifier()

        dual = _profile(military_apps=["targeting"], commercial_apps=["mapping"])
        assert classifier.classify_category(dual) == "dual_use"

        mil = _profile(military_apps=["targeting"], commercial_apps=[])
        assert classifier.classify_category(mil) == "military_only"

        com = _profile(military_apps=[], commercial_apps=["mapping"])
        assert classifier.classify_category(com) == "commercial_only"

        neither = _profile(military_apps=[], commercial_apps=[])
        assert classifier.classify_category(neither) == "neither"

    def test_regulatory_flag(self):
        """Regulatory flags should be set based on export control and dual-use status."""
        classifier = DualUseClassifier()

        itar = _profile(
            category="defense",
            military_apps=["targeting"],
            commercial_apps=["mapping"],
            export_control="ITAR",
        )
        flags = classifier.regulatory_flags(itar)
        assert isinstance(flags, list)
        assert "ITAR_CONTROLLED" in flags
        assert len(flags) > 0

        ear = _profile(
            category="dual_use",
            military_apps=["targeting"],
            commercial_apps=["mapping"],
            export_control="EAR",
        )
        ear_flags = classifier.regulatory_flags(ear)
        assert "EAR_CONTROLLED" in ear_flags
        assert "DUAL_USE_REVIEW_REQUIRED" in ear_flags

    def test_classification_report(self):
        """Report should aggregate classification results."""
        classifier = DualUseClassifier()
        results = [
            classifier.classify(
                _profile(
                    military_apps=["targeting", "radar", "ew"],
                    commercial_apps=["weather", "mapping", "nav"],
                    category="dual_use",
                )
            ),
            classifier.classify(
                _profile(military_apps=["targeting"], commercial_apps=[], category="defense")
            ),
            classifier.classify(
                _profile(military_apps=[], commercial_apps=["mapping"], category="commercial")
            ),
        ]
        report = classifier.generate_classification_report(results)
        assert isinstance(report, dict)
        assert report["total"] == 3
        assert 0.0 <= report["average_dual_use_score"] <= 1.0
        assert isinstance(report["by_classification"], dict)
        assert report["dual_use_count"] >= 1

        empty_report = classifier.generate_classification_report([])
        assert empty_report["total"] == 0
        assert empty_report["average_dual_use_score"] == 0.0
