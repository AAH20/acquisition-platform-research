"""Tests for the consolidated reporting module."""

from acquisition_platform.reporting import Report, generate_report


class TestReportCreation:
    def test_create_report_with_title(self):
        report = Report(title="Test Report")
        assert report.title == "Test Report"

    def test_create_report_with_metadata(self):
        report = Report(title="Test", metadata={"analyst": "Alice"})
        assert report.metadata["analyst"] == "Alice"

    def test_create_empty_report(self):
        report = Report()
        assert report.title == "Acquisition Platform Report"
        assert report.sections == {}


class TestReportAggregation:
    def test_add_section(self):
        report = Report()
        report.add_section("matches", [{"buyer_id": "b1", "seller_id": "s1"}])
        assert "matches" in report.sections
        assert len(report.sections["matches"]) == 1

    def test_add_matches(self):
        report = Report()
        report.add_matches([{"buyer_id": "b1", "seller_id": "s1"}])
        assert "matches" in report.sections

    def test_add_valuation(self):
        report = Report()
        report.add_valuation({"value": 100000, "method": "DCF"})
        assert "valuation" in report.sections

    def test_add_valuations(self):
        report = Report()
        report.add_valuations([{"value": 100000}, {"value": 200000}])
        assert len(report.sections["valuation"]) == 2

    def test_add_fraud_scores(self):
        report = Report()
        report.add_fraud_scores([{"score": 0.1, "risk_level": "low"}])
        assert "fraud_scores" in report.sections

    def test_add_portfolio(self):
        report = Report()
        report.add_portfolio({"assets": ["a1", "a2"]})
        assert "portfolio" in report.sections

    def test_add_price_recommendation(self):
        report = Report()
        report.add_price_recommendation({"recommended_price": 100000})
        assert "price_recommendation" in report.sections

    def test_add_entity_clusters(self):
        report = Report()
        report.add_entity_clusters([{"canonical_name": "Acme Corp"}])
        assert "entity_clusters" in report.sections

    def test_add_ranked_listings(self):
        report = Report()
        report.add_ranked_listings([{"id": "l1", "score": 0.9}])
        assert "ranked_listings" in report.sections

    def test_add_evolution(self):
        report = Report()
        report.add_evolution({"best_fitness": 0.95})
        assert "evolution" in report.sections


class TestReportExport:
    def test_to_dict(self):
        report = Report(title="Test", metadata={"key": "value"})
        report.add_section("matches", [{"buyer_id": "b1"}])
        d = report.to_dict()
        assert d["title"] == "Test"
        assert d["metadata"]["key"] == "value"
        assert "matches" in d["sections"]

    def test_to_json(self):
        report = Report(title="Test")
        report.add_section("matches", [{"buyer_id": "b1"}])
        json_str = report.to_json()
        assert '"title": "Test"' in json_str
        assert '"matches"' in json_str

    def test_to_csv(self):
        report = Report()
        report.add_section("matches", [{"buyer_id": "b1", "seller_id": "s1"}])
        csv_str = report.to_csv()
        assert "section" in csv_str
        assert "matches" in csv_str
        assert "b1" in csv_str

    def test_to_csv_empty(self):
        report = Report()
        csv_str = report.to_csv()
        assert "section" in csv_str

    def test_to_markdown(self):
        report = Report(title="Test Report")
        report.add_section("matches", [{"buyer_id": "b1", "seller_id": "s1"}])
        md = report.to_markdown()
        assert "# Test Report" in md
        assert "## Matches" in md
        assert "b1" in md

    def test_to_markdown_with_metadata(self):
        report = Report(title="Test", metadata={"analyst": "Alice"})
        md = report.to_markdown()
        assert "Alice" in md


class TestGenerateReport:
    def test_generate_report_with_matches(self):
        report = generate_report(matches=[{"buyer_id": "b1"}])
        assert "matches" in report.sections

    def test_generate_report_with_valuations(self):
        report = generate_report(valuations=[{"value": 100000}])
        assert "valuation" in report.sections

    def test_generate_report_with_fraud_scores(self):
        report = generate_report(fraud_scores=[{"score": 0.1}])
        assert "fraud_scores" in report.sections

    def test_generate_report_with_portfolio(self):
        report = generate_report(portfolio={"assets": ["a1"]})
        assert "portfolio" in report.sections

    def test_generate_report_with_price_recommendation(self):
        report = generate_report(price_recommendation={"recommended_price": 100000})
        assert "price_recommendation" in report.sections

    def test_generate_report_with_entity_clusters(self):
        report = generate_report(entity_clusters=[{"canonical_name": "Acme"}])
        assert "entity_clusters" in report.sections

    def test_generate_report_with_ranked_listings(self):
        report = generate_report(ranked_listings=[{"id": "l1"}])
        assert "ranked_listings" in report.sections

    def test_generate_report_with_evolution(self):
        report = generate_report(evolution={"best_fitness": 0.95})
        assert "evolution" in report.sections

    def test_generate_report_with_all_sections(self):
        report = generate_report(
            title="Full Report",
            metadata={"analyst": "Alice"},
            matches=[{"buyer_id": "b1"}],
            valuations=[{"value": 100000}],
            fraud_scores=[{"score": 0.1}],
            portfolio={"assets": ["a1"]},
            price_recommendation={"recommended_price": 100000},
            entity_clusters=[{"canonical_name": "Acme"}],
            ranked_listings=[{"id": "l1"}],
            evolution={"best_fitness": 0.95},
        )
        assert report.title == "Full Report"
        assert len(report.sections) == 8

    def test_generate_report_empty(self):
        report = generate_report()
        assert report.sections == {}
