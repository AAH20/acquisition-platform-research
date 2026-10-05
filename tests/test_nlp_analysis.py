"""Tests for NLP document analysis module."""
import pytest

from acquisition_platform.nlp_analysis import (
    Document,
    NLPAnalyzer,
    NLPResult,
)


class TestNLPAnalyzer:
    """TDD tests for the NLP document analysis module."""

    def test_entity_extraction(self):
        """Entities extracted from text."""
        analyzer = NLPAnalyzer()
        text = "Apple Inc. was founded by Steve Jobs in Cupertino, California. Google and Microsoft are competitors."
        entities = analyzer.extract_entities(text)
        assert isinstance(entities, list)
        assert len(entities) > 0
        # Should extract company names and person names
        assert any("Apple" in e for e in entities)
        assert any("Steve Jobs" in e for e in entities)

    def test_sentiment_analysis(self):
        """Sentiment scored between -1 and 1."""
        analyzer = NLPAnalyzer()
        positive_text = "This is an excellent product with amazing quality and outstanding performance."
        negative_text = "This is a terrible product with awful quality and horrible performance."
        neutral_text = "The product is a standard item with typical features."

        pos_score = analyzer.sentiment_analysis(positive_text)
        neg_score = analyzer.sentiment_analysis(negative_text)
        neu_score = analyzer.sentiment_analysis(neutral_text)

        assert isinstance(pos_score, float)
        assert -1.0 <= pos_score <= 1.0
        assert pos_score > 0.0
        assert neg_score < 0.0
        assert abs(neu_score) < abs(pos_score)

    def test_empty_document(self):
        """Empty document returns defaults."""
        analyzer = NLPAnalyzer()
        doc = Document(doc_id="empty-1", text="", source="test", date="2024-01-01")
        result = analyzer.generate_nlp_report(doc)
        assert isinstance(result, NLPResult)
        assert result.doc == doc
        assert result.entities == []
        assert result.sentiment == 0.0
        assert result.keywords == []
        assert result.topics == []
        assert result.summary == ""

    def test_keyword_extraction(self):
        """Keywords extracted from text."""
        analyzer = NLPAnalyzer()
        text = "Machine learning and artificial intelligence are transforming the technology industry with neural networks and deep learning."
        keywords = analyzer.extract_keywords(text)
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # Should extract meaningful terms
        assert any("learning" in k.lower() for k in keywords)

    def test_topic_modeling(self):
        """Topics identified from text."""
        analyzer = NLPAnalyzer()
        text = "The stock market showed strong growth today. Investors are optimistic about technology stocks and financial markets. The economy is recovering."
        topics = analyzer.topic_modeling(text)
        assert isinstance(topics, list)
        assert len(topics) > 0
        assert all(isinstance(t, str) for t in topics)

    def test_document_classification(self):
        """Document classified into a category."""
        analyzer = NLPAnalyzer()
        tech_text = "The new software framework uses machine learning algorithms and cloud computing infrastructure."
        finance_text = "The company reported strong quarterly earnings with revenue growth and profit margins."

        tech_class = analyzer.classify_document(tech_text)
        finance_class = analyzer.classify_document(finance_text)

        assert isinstance(tech_class, str)
        assert len(tech_class) > 0
        assert isinstance(finance_class, str)
        assert len(finance_class) > 0

    def test_nlp_report(self):
        """Full NLP report generated."""
        analyzer = NLPAnalyzer()
        doc = Document(
            doc_id="doc-1",
            text="Apple announced record iPhone sales. The company exceeded analyst expectations with strong revenue growth.",
            source="news",
            date="2024-01-15",
        )
        report = analyzer.generate_nlp_report(doc)
        assert isinstance(report, NLPResult)
        assert report.doc == doc
        assert isinstance(report.entities, list)
        assert isinstance(report.sentiment, float)
        assert isinstance(report.keywords, list)
        assert isinstance(report.topics, list)
        assert isinstance(report.summary, str)

    def test_summarization(self):
        """Summary generated from text."""
        analyzer = NLPAnalyzer()
        text = (
            "The technology sector experienced significant growth in the third quarter. "
            "Major companies reported strong earnings driven by cloud computing and AI adoption. "
            "Analysts predict continued expansion in the coming months. "
            "Investment in research and development reached record levels."
        )
        summary = analyzer.summarize(text)
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert len(summary) < len(text)

    def test_similarity(self):
        """Similarity scored between two texts."""
        analyzer = NLPAnalyzer()
        text1 = "Machine learning is transforming the technology industry."
        text2 = "Machine learning and artificial intelligence are transforming the technology industry."
        text3 = "The weather today is sunny and warm."

        sim_similar = analyzer.similarity(text1, text2)
        sim_different = analyzer.similarity(text1, text3)

        assert isinstance(sim_similar, float)
        assert 0.0 <= sim_similar <= 1.0
        assert isinstance(sim_different, float)
        assert 0.0 <= sim_different <= 1.0
        assert sim_similar > sim_different

    def test_language_detection(self):
        """Language detected from text."""
        analyzer = NLPAnalyzer()
        en_text = "This is a sample English document for language detection."
        es_text = "Este es un documento de ejemplo en español para detección de idioma."
        fr_text = "Ceci est un document exemple en français pour la détection de langue."

        en_lang = analyzer.detect_language(en_text)
        es_lang = analyzer.detect_language(es_text)
        fr_lang = analyzer.detect_language(fr_text)

        assert isinstance(en_lang, str)
        assert en_lang == "en"
        assert isinstance(es_lang, str)
        assert es_lang == "es"
        assert isinstance(fr_lang, str)
        assert fr_lang == "fr"
