"""NLP document analysis module.

Entity extraction, sentiment analysis, keyword extraction,
topic modeling, document classification, summarization,
similarity scoring, and language detection for acquisition research.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Set

from acquisition_platform.exceptions import ValidationError
from acquisition_platform.observability import get_logger, log_execution_time, log_module_call
from acquisition_platform.serialization import SerializableMixin

logger = get_logger(__name__)

# Stop words for keyword extraction
_STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "need", "dare",
    "this", "that", "these", "those", "it", "its", "i", "you", "he",
    "she", "we", "they", "me", "him", "her", "us", "them", "my", "your",
    "his", "our", "their", "what", "which", "who", "whom", "when",
    "where", "why", "how", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "because", "as", "until",
    "while", "about", "between", "through", "during", "before", "after",
    "above", "below", "up", "down", "out", "off", "over", "under", "again",
    "further", "then", "once", "here", "there", "also",
}

# Positive and negative word lists for sentiment analysis
_POSITIVE_WORDS: Set[str] = {
    "excellent", "amazing", "outstanding", "strong", "growth", "optimistic",
    "positive", "success", "successful", "profit", "profitable", "gain",
    "benefit", "beneficial", "improve", "improved", "improvement", "best",
    "better", "good", "great", "high", "higher", "increase", "increased",
    "innovative", "innovation", "leader", "leading", "opportunity",
    "opportunities", "promising", "robust", "surge", "surged", "thrive",
    "thriving", "upside", "win", "winning", "record", "exceeded", "expansion",
    "recovering", "recovery", "bullish", "breakthrough", "dominant",
}

_NEGATIVE_WORDS: Set[str] = {
    "terrible", "awful", "horrible", "poor", "weak", "decline", "declined",
    "loss", "losses", "fail", "failed", "failure", "negative", "worse",
    "worst", "bad", "low", "lower", "decrease", "decreased", "risk",
    "risks", "risky", "threat", "threats", "crisis", "crash", "bearish",
    "concern", "concerns", "worried", "worry", "volatile", "volatility",
    "uncertainty", "uncertain", "recession", "bankrupt", "bankruptcy",
    "layoff", "layoffs", "downgrade", "downgraded", "miss", "missed",
    "disappointing", "disappointed", "struggle", "struggling", "trouble",
}

# Topic keywords for classification
_TOPIC_KEYWORDS: dict[str, Set[str]] = {
    "technology": {
        "software", "hardware", "cloud", "computing", "ai", "artificial",
        "intelligence", "machine", "learning", "data", "digital", "cyber",
        "security", "network", "platform", "app", "application", "algorithm",
        "automation", "robotics", "semiconductor", "chip", "tech",
    },
    "finance": {
        "revenue", "profit", "earnings", "financial", "investment", "investor",
        "stock", "market", "capital", "funding", "valuation", "dividend",
        "balance", "sheet", "income", "expense", "margin", "cash", "flow",
        "portfolio", "asset", "liability", "equity", "bond", "trading",
    },
    "healthcare": {
        "health", "medical", "pharmaceutical", "drug", "clinical", "patient",
        "treatment", "therapy", "disease", "diagnosis", "hospital", "doctor",
        "biotech", "vaccine", "fda", "approval", "trial",
    },
    "energy": {
        "energy", "oil", "gas", "renewable", "solar", "wind", "power",
        "electric", "grid", "carbon", "emission", "sustainable", "green",
        "fossil", "nuclear", "utility",
    },
    "legal": {
        "law", "legal", "regulation", "regulatory", "compliance", "court",
        "litigation", "patent", "trademark", "copyright", "license",
        "settlement", "lawsuit", "antitrust", "governance",
    },
    "operations": {
        "manufacturing", "supply", "chain", "logistics", "production",
        "inventory", "warehouse", "distribution", "procurement", "quality",
        "efficiency", "process", "operations", "facility", "plant",
    },
}

# Language detection stopwords
_LANGUAGE_STOPWORDS: dict[str, Set[str]] = {
    "en": {
        "the", "is", "are", "was", "were", "be", "been", "being", "have",
        "has", "had", "do", "does", "did", "will", "would", "could", "should",
        "this", "that", "these", "those", "it", "its", "and", "or", "but",
        "in", "on", "at", "to", "for", "of", "with", "by", "from", "as",
    },
    "es": {
        "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
        "en", "y", "o", "pero", "por", "para", "con", "sin", "sobre", "entre",
        "es", "son", "fue", "ser", "estar", "este", "esta", "esto", "ese", "esa",
    },
    "fr": {
        "le", "la", "les", "un", "une", "des", "de", "du", "en", "et", "ou",
        "mais", "pour", "par", "avec", "sans", "sur", "entre", "est", "sont",
        "a", "avoir", "être", "ce", "cette", "ces", "il", "elle", "ils", "elles",
    },
    "de": {
        "der", "die", "das", "ein", "eine", "einer", "eines", "einem", "einen",
        "und", "oder", "aber", "für", "mit", "ohne", "auf", "in", "an", "zu",
        "ist", "sind", "war", "waren", "sein", "haben", "hat", "hatte", "dieser",
        "diese", "dieses",
    },
}


@dataclass
class Document(SerializableMixin):
    """A document for NLP analysis.

    Attributes:
        doc_id: Unique document identifier.
        text: Document text content.
        source: Document source (e.g. "news", "filing", "report").
        date: Document date string.
    """

    doc_id: str
    text: str
    source: str
    date: str


@dataclass
class NLPResult(SerializableMixin):
    """Result of NLP analysis on a document.

    Attributes:
        doc: The analyzed document.
        entities: Extracted named entities.
        sentiment: Sentiment score (-1 to 1).
        keywords: Extracted keywords.
        topics: Identified topics.
        summary: Generated summary.
    """

    doc: Document
    entities: list[str] = field(default_factory=list)
    sentiment: float = 0.0
    keywords: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    summary: str = ""


class NLPAnalyzer:
    """NLP document analyzer for acquisition research.

    Provides entity extraction, sentiment analysis, keyword extraction,
    topic modeling, document classification, summarization, similarity
    scoring, and language detection.
    """

    def __init__(self) -> None:
        """Initialize the NLP analyzer."""
        self._logger = get_logger(__name__)

    @log_execution_time(logger)
    def extract_entities(self, text: str) -> list[str]:
        """Extract named entities from text.

        Uses pattern matching to identify company names, person names,
        and locations.

        Args:
            text: Input text to analyze.

        Returns:
            List of extracted entity strings.
        """
        if not text or not text.strip():
            return []

        entities: list[str] = []

        # Extract company names (Inc., Corp., Ltd., LLC, etc.)
        company_pattern = r"\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*\s+(?:Inc\.?|Corp\.?|Ltd\.?|LLC|PLC|AG|SA|NV|Co\.?)\b"
        companies = re.findall(company_pattern, text)
        entities.extend(companies)

        # Extract person names (First Last pattern, 2-3 words)
        person_pattern = r"\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b"
        persons = re.findall(person_pattern, text)
        # Filter out common false positives
        false_positives = {"New York", "San Francisco", "Los Angeles", "United States"}
        persons = [p for p in persons if p not in false_positives]
        entities.extend(persons)

        # Extract capitalized phrases (potential entities)
        cap_pattern = r"\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)+\b"
        caps = re.findall(cap_pattern, text)
        for cap in caps:
            if cap not in entities and cap not in false_positives:
                entities.append(cap)

        # Deduplicate while preserving order
        seen: Set[str] = set()
        unique_entities: list[str] = []
        for entity in entities:
            entity = entity.strip()
            if entity and entity not in seen:
                seen.add(entity)
                unique_entities.append(entity)

        return unique_entities

    @log_execution_time(logger)
    def sentiment_analysis(self, text: str) -> float:
        """Analyze sentiment of text.

        Returns a score between -1 (very negative) and 1 (very positive).

        Args:
            text: Input text to analyze.

        Returns:
            Sentiment score between -1 and 1.
        """
        if not text or not text.strip():
            return 0.0

        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        if not words:
            return 0.0

        pos_count = sum(1 for w in words if w in _POSITIVE_WORDS)
        neg_count = sum(1 for w in words if w in _NEGATIVE_WORDS)
        total = pos_count + neg_count

        if total == 0:
            return 0.0

        return (pos_count - neg_count) / total

    @log_execution_time(logger)
    def extract_keywords(self, text: str, top_n: int = 10) -> list[str]:
        """Extract keywords from text.

        Uses frequency analysis with stopword removal.

        Args:
            text: Input text to analyze.
            top_n: Maximum number of keywords to return.

        Returns:
            List of extracted keywords.
        """
        if not text or not text.strip():
            return []

        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        filtered = [w for w in words if w not in _STOP_WORDS and len(w) > 2]

        if not filtered:
            return []

        counter = Counter(filtered)
        return [word for word, _ in counter.most_common(top_n)]

    @log_execution_time(logger)
    def topic_modeling(self, text: str) -> list[str]:
        """Identify topics in text.

        Uses keyword matching against predefined topic categories.

        Args:
            text: Input text to analyze.

        Returns:
            List of identified topic strings.
        """
        if not text or not text.strip():
            return []

        words = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
        if not words:
            return []

        topic_scores: dict[str, int] = {}
        for topic, keywords in _TOPIC_KEYWORDS.items():
            score = len(words & keywords)
            if score > 0:
                topic_scores[topic] = score

        # Sort by score descending
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, _ in sorted_topics]

    @log_execution_time(logger)
    def classify_document(self, text: str) -> str:
        """Classify document into a category.

        Args:
            text: Input text to classify.

        Returns:
            Document category string.
        """
        if not text or not text.strip():
            return "unknown"

        topics = self.topic_modeling(text)
        if topics:
            return topics[0]

        return "general"

    @log_execution_time(logger)
    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """Generate a summary of the text.

        Extracts the most important sentences based on keyword density.

        Args:
            text: Input text to summarize.
            max_sentences: Maximum number of sentences in summary.

        Returns:
            Summary string.
        """
        if not text or not text.strip():
            return ""

        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        if len(sentences) <= max_sentences:
            return text.strip()

        # Score sentences by keyword density
        keywords = set(self.extract_keywords(text, top_n=20))
        sentence_scores: list[tuple[str, float]] = []
        for sentence in sentences:
            words = set(re.findall(r"\b[a-zA-Z]+\b", sentence.lower()))
            if not words:
                continue
            score = len(words & keywords) / len(words)
            sentence_scores.append((sentence, score))

        # Sort by score and take top N
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s for s, _ in sentence_scores[:max_sentences]]

        # Restore original order
        ordered = [s for s in sentences if s in top_sentences]
        return " ".join(ordered)

    @log_execution_time(logger)
    def similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts.

        Uses Jaccard similarity on word sets.

        Args:
            text1: First text.
            text2: Second text.

        Returns:
            Similarity score between 0 and 1.
        """
        if not text1 or not text2:
            return 0.0

        words1 = set(re.findall(r"\b[a-zA-Z]+\b", text1.lower()))
        words2 = set(re.findall(r"\b[a-zA-Z]+\b", text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    @log_execution_time(logger)
    def detect_language(self, text: str) -> str:
        """Detect the language of text.

        Uses stopword frequency analysis.

        Args:
            text: Input text to analyze.

        Returns:
            ISO 639-1 language code (e.g. "en", "es", "fr").
        """
        if not text or not text.strip():
            return "unknown"

        words = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
        if not words:
            return "unknown"

        lang_scores: dict[str, int] = {}
        for lang, stopwords in _LANGUAGE_STOPWORDS.items():
            score = len(words & stopwords)
            if score > 0:
                lang_scores[lang] = score

        if not lang_scores:
            return "unknown"

        return max(lang_scores, key=lambda k: lang_scores[k])

    @log_execution_time(logger)
    def generate_nlp_report(self, doc: Document) -> NLPResult:
        """Generate a full NLP analysis report for a document.

        Args:
            doc: Document to analyze.

        Returns:
            NLPResult with all analysis outputs.
        """
        if not doc.text or not doc.text.strip():
            return NLPResult(doc=doc)

        entities = self.extract_entities(doc.text)
        sentiment = self.sentiment_analysis(doc.text)
        keywords = self.extract_keywords(doc.text)
        topics = self.topic_modeling(doc.text)
        summary = self.summarize(doc.text)

        return NLPResult(
            doc=doc,
            entities=entities,
            sentiment=sentiment,
            keywords=keywords,
            topics=topics,
            summary=summary,
        )
