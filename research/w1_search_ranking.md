# Wave 1 Research: Search Ranking for Business Marketplace Listings

**Date:** 2026-10-04  
**Focus:** Search ranking algorithms, methods, and optimization for business marketplace listings  
**Search Queries:** 10 parallel web searches covering ranking methods, algorithms, relevance, ML, bottlenecks, optimization, NP-hard problems, learning to rank, user behavior, and personalization

---

## Executive Summary

Search ranking is the core mechanism that determines which business listings appear in response to user queries on marketplace platforms. Modern ranking systems combine classical information retrieval methods (BM25, TF-IDF, PageRank) with machine learning approaches (Learning to Rank, neural rankers) and user behavior signals (clicks, dwell time, conversions). The field faces fundamental computational limits—many ranking optimization problems are NP-hard—and practical bottlenecks including latency constraints, cold-start problems, and the tension between relevance and monetization. Personalization adds another layer of complexity, as rankings must adapt to individual user context while maintaining fairness and transparency.

---

## 1. Ranking Methods

### 1.1 Classical Retrieval-Based Ranking

| Method | Description | Use Case |
|--------|-------------|----------|
| **BM25** | Probabilistic ranking function based on term frequency, inverse document frequency, and document length normalization | Baseline text relevance scoring |
| **TF-IDF** | Term frequency–inverse document frequency weighting | Classic document retrieval |
| **PageRank** | Link-analysis algorithm measuring page importance via eigenvector computation | Web page authority scoring |
| **HITS** | Hyperlink-Induced Topic Search; identifies hubs and authorities | Blog and content ranking |
| **Weighted PageRank** | Extension of PageRank considering both inlink and outlink importance | Enhanced web ranking |
| **Distance Rank** | Reinforcement-learning-based recursive method using shortest logarithmic distance between pages | Specialized page ranking |
| **EigenRumor** | Ranks blog entries by weighting hub/authority scores of bloggers | Blog-specific ranking |

**Key Insight:** Classical methods remain foundational. Modern systems use BM25 as a baseline feature within larger learned ranking pipelines rather than as standalone rankers.

### 1.2 Learning to Rank (LTR) Methods

| Approach | Description | Examples |
|----------|-------------|----------|
| **Pointwise** | Treats ranking as independent prediction per query-document pair; any classifier/regressor works | Logistic regression, gradient-boosted trees |
| **Pairwise** | Learns relative order between document pairs; optimizes pairwise comparisons | RankNet, RankBoost |
| **Listwise** | Directly optimizes entire ranked list quality; targets NDCG | ListNet, ListMLE, LambdaMART |

**Key Insight:** Listwise approaches generally achieve superior performance on benchmarks by aligning more closely with end-to-end ranking objectives. LambdaMART won the 2010 Yahoo! Learning-to-Rank Challenge and remains a production baseline.

### 1.3 Two-Stage Retrieve-and-Rerank Architecture

Modern marketplace search systems universally employ a two-stage architecture:
1. **Retrieval stage:** Cheap query (BM25, boolean filters) collects a candidate window (typically 100–1000 items)
2. **Reranking stage:** Expensive ML model (LambdaMART, neural ranker) re-scores only the top-N candidates

This bounds latency because expensive feature computation and model inference touch only the top-N documents, not the entire index.

---

## 2. Algorithms

### 2.1 RankNet (2005)
- **Author:** Chris Burges et al., Microsoft Research
- **Mechanism:** Probabilistic cost function over document pairs using sigmoid function based on score difference
- **Training:** Backpropagation with cross-entropy loss
- **Significance:** First neural pairwise LTR model; demonstrated that learned neural rankers outperform hand-tuned formulas on real commercial search data

### 2.2 LambdaRank (2006)
- **Mechanism:** Defines gradient (lambda) directly without a differentiable surrogate loss
- **Formula:** λ_ij = |ΔNDCG| × pairwise_gradient_ij^RankNet
- **Insight:** Focuses learning effort on document swaps that matter most to NDCG
- **Result:** Consistently improved NDCG on held-out test queries, outperforming both RankNet and pointwise baselines

### 2.3 LambdaMART
- **Mechanism:** Combines LambdaRank's metric-aware gradients with gradient-boosted decision trees (MART)
- **Advantage:** Faster training and inference than neural networks on structured feature data
- **Achievement:** Won Track 1 of 2010 Yahoo! Learning-to-Rank Challenge

### 2.4 RankBrain (Google, 2015)
- Google's first ML ranking component
- Uses deep learning to interpret queries and match them to results
- Processes a significant percentage of Google queries

### 2.5 DeepRank
- LLM-based system built on BERT-style architecture
- Decomposes complex ranking signals using transformer-based representations

### 2.6 Navboost
- Google's click-based signal system aggregating user interactions over 13 months
- Described as "just a big table" mapping queries to documents and aggregated click counts
- Serves as implicit human judgment signal

---

## 3. Relevance

### 3.1 Relevance Signals (2024–2026)

Modern search ranking incorporates 200+ documented signals, but only ~12 carry measurable weight in controlled A/B tests:

| Signal | Description | Weight |
|--------|-------------|--------|
| **Page Experience** | Core Web Vitals: LCP ≤ 2.5s, FID ≤ 100ms, CLS ≤ 0.1 | Top-tier |
| **Entity Salience** | BERT-based embeddings matching named entities in query and document | Top-tier |
| **User Engagement Velocity** | CTR within first 300ms of SERP load (weighted 3.7× more than CTR after 1s) | Top-tier |
| **Domain Authority** | Correlated with top-10 rankings at r = 0.31 (down from r = 0.58 in 2018) | Declining |
| **Semantic Coherence** | Sentence-level BERTScore between query and content (r = 0.64 correlation with position 1) | Rising |

### 3.2 Relevance vs. Intent
Search engines now parse intent rather than match strings. For example, "Canon EOS R6 Mark II battery life video" triggers different ranking logic than "Canon EOS R6 Mark II battery specs PDF" even when both return pages from the same domain.

### 3.3 Zero-Click Searches
- Featured snippets capture 41% of 'how-to' queries and 68% of unit-conversion requests
- Reduces organic click-through rates for those terms by up to 72%
- Commercial queries retain higher CTR with Shopping Ads occupying top positions

---

## 4. Machine Learning in Search Ranking

### 4.1 ML-Driven Ranking Pipeline

Google's transition to ML-based ranking (integrated 2018):
- **Before:** Hundreds of manually tuned weights and factors
- **After:** ML models trained on usage logs from the last four weeks
- **Training data:** Each click = label 1, non-click = label 0; each search impression with a click becomes a training example
- **Model:** TensorFlow Ranking; daily model rollouts
- **Measurement:** Offline analysis (replaying queries from logs) + live A/B experimentation

### 4.2 Feature Engineering for Marketplace Ranking

Features fall into three families:

| Feature Type | Description | Examples |
|--------------|-------------|----------|
| **Query-dependent** | Depend on both query and document | BM25 on title, BM25 on body, phrase-match flags |
| **Document-only** | Depend only on the document | Popularity (log of views), recency (gaussian decay), in-stock flags, average rating |
| **Query-only** | Depend only on the query | Token count, detected intent class |

### 4.3 ML Model Training for Marketplaces

- **Objective:** `rank:ndcg` (listwise LambdaMART-style) or `rank:pairwise`
- **Algorithm:** XGBoost with max_depth 4–8, learning rate 0.05–0.3
- **Labels:** Graded relevance (0 = irrelevant, 1 = marginal, 2 = relevant, 3 = perfect)
- **Deployment:** Model kept in memory; inference in milliseconds

### 4.4 Word Embeddings
- Outperform manually defined synonyms
- Reduce reliance on human curation, especially on the "long tail" of search queries

---

## 5. Bottlenecks

### 5.1 Latency Constraints

| Metric | Google | Bing | DuckDuckGo |
|--------|--------|------|------------|
| Median Query Latency (desktop) | 238 ms | 312 ms | 487 ms |
| Daily Query Volume | 8.5B | 1.5B | 126M |
| Index Size (estimated) | 130B pages | 110B pages | 1.2B pages |

- Users abandon queries after 2.3 seconds (median abandonment threshold)
- Users rarely see results ranked #11–#20 regardless of objective quality
- TTFB varies by geography: Tokyo 142ms, Frankfurt 187ms, São Paulo 294ms, Nairobi 511ms

### 5.2 Indexing Bottlenecks

| Blocker | Detection | Typical Fix Time |
|---------|-----------|-----------------|
| robots.txt disallow | GSC → Settings → robots.txt tester | Same day |
| Server 5xx errors | GSC → Crawl stats → host status | 1–3 days |
| Orphan pages | Screaming Frog → Internal links report | 1–2 weeks |
| Slow server response | GSC → Crawl stats → average response time | 1–4 weeks |
| Crawl budget exhaustion | Log file analysis | 2–6 weeks |
| Unrendered JS content | Mobile-Friendly Test → rendered HTML check | 2–8 weeks |

### 5.3 Content Quality Bottlenecks
- Thin or duplicate content is the leading cause of "crawled — currently not indexed" status
- Pages get crawled successfully then quietly excluded weeks later once quality systems evaluate them
- Canonicalization signals can silently de-index thousands of pages via a single misconfigured template

### 5.4 AI Search Disruption
- AI Overviews have cut organic CTR by 61% on affected queries
- Only 38% of pages cited in Google's AI Overviews also rank in the top 10 (down from 76% seven months earlier)
- 89% of citation surface is engine-specific (only 11% of cited domains appear on more than one AI engine)
- 615× citation volume variance between platforms for the same brand

### 5.5 Feature Pipeline Bottlenecks
- Training/serving skew: feature pipeline must produce identical values at training and serving time
- Judgment-collection process needs continuous refresh as catalog and query mix drift
- Retraining cadence requires its own evaluation gates

---

## 6. Optimization

### 6.1 Ranking Optimization Strategies

| Strategy | Description |
|----------|-------------|
| **Keyword optimization** | Boost webpages containing specific terms |
| **Weighted labels** | Promote/demote sites with weights from -1.0 to +1.0 |
| **Score-based ranking** | Apply scores to individual annotations (-1.0 to 1.0) |
| **Internal linking** | Encourage discovery of new pages via anchor text |
| **Content quality** | Produce human-focused, people-first content |
| **On-page SEO** | Optimize titles, subsections, images, videos |
| **Local SEO** | Location pages, local keywords, Google Business Profile |

### 6.2 Automated Optimization
- Google's ML-driven approach eliminates manual formula tweaking
- Small teams operate driven by usage data only
- No human raters needed for internal search
- Daily ranking model rollouts with automatic validation

### 6.3 A/B Testing for Ranking
- Divert a share of traffic to a different ranking model for direct comparison
- Combine offline analysis (replaying queries from logs) with live experimentation
- Measure whether clicked results rank higher on average

---

## 7. NP-Hard Problems in Search Ranking

### 7.1 Fundamental Computational Limits

Many ranking optimization problems are NP-hard:

| Problem | Complexity | Implication |
|---------|------------|-------------|
| **Novelty/diversity ranking** | NP-hard (Agrawal et al. 2009; Clarke et al. 2008; Zhai et al. 2008) | Finding maximum novelty at a given rank is computationally intractable |
| **Optimal ranking with competing objectives** | NP-hard | Cannot find globally optimal ranking across high-dimensional feature space |
| **Ulam rank aggregation** | NP-hard to approximate within 35/34 − ε for four rankings | Even aggregating just four input rankings is intractable |
| **Kendall-tau median** | Polynomial-time solvable (PTAS exists) | Contrast with Ulam metric hardness |

### 7.2 Practical Implications

- **Architectural debt:** Systems that approximate NP-hard problems work at current scale but fail when adding ranking signals, constraints, or corpus size
- **Heuristic limitations:** Greedy algorithms with known approximation bounds are the practical approach
- **Problem reframing:** Define tractable subsets—optimize for relevance alone, pre-filter to manageable candidate sets, or use greedy algorithms with known bounds
- **Honest claims:** "Best we found in reasonable time" ≠ "best possible"

### 7.3 Rank Aggregation Hardness
- Ulam median problem: NP-hard for unbounded input rankings
- Best-known polynomial-time approximation factor: 1.968
- For three input permutations: polynomial-time solvable
- For four input rankings: NP-hard to approximate within 35/34 − ε (unless P = NP)

---

## 8. Learning to Rank (LTR)

### 8.1 Formal Problem Definition

Given:
- Query q
- Candidate documents D_q = {d_j}_{j=1}^m
- Relevance labels r_d for each document

Goal: Learn ranking function f(q, d) that outputs real-valued scores for sorting documents in descending order of relevance.

### 8.2 Three Architectural Approaches

| Approach | Unit of Comparison | Strengths | Weaknesses |
|----------|-------------------|-----------|------------|
| **Pointwise** | Single query-document pair | Any standard classifier works; simple | Cannot understand document order relative to each other |
| **Pairwise** | Document pairs | Explicitly optimizes relative order | O(n²) comparisons; doesn't capture full list context |
| **Listwise** | Entire ranked list | Targets NDCG directly; best benchmark performance | NDCG non-differentiability problem |

### 8.3 NDCG Non-Differentiability Problem
- NDCG uses discrete rank positions → cannot directly use gradient descent
- **LambdaRank solution:** Define proxy gradient as RankNet pairwise gradient scaled by NDCG delta from swapping each document pair
- Lambdas behave like proper gradients for gradient descent despite not being gradients of any explicit loss function

### 8.4 LTR in Production

| Component | Role |
|-----------|------|
| **Hand-crafted signals** | PageRank, TF-IDF, entity match, freshness, structured data, mobile-friendliness (majority still manually engineered) |
| **Learned ranking model** | Takes signals as input features; learns optimal combination per query type |
| **ML components** | RankBrain, DeepRank contribute additional features or post-processing layers |
| **Click-based systems** | Navboost provides usage signals as implicit human judgments |

### 8.5 LTR Performance Gains
- Up to 16% higher MAP compared to BM25 baselines in two-stage pipelines
- ListNet improved mean average precision by up to 10% over pairwise baselines on TREC Web Track
- Amazon's RankFormer (Transformer-based listwise LTR): 13.7% lift in revenue

---

## 9. User Behavior

### 9.1 Behavior-Based Ranking Signals

| Signal | Description | Impact |
|--------|-------------|--------|
| **Click-through rate (CTR)** | Probability of click given impression | Primary implicit feedback signal |
| **Dwell time** | Time spent on clicked result | Quality indicator |
| **User Engagement Velocity** | CTR within first 300ms of SERP load | Weighted 3.7× more than CTR after 1s |
| **Click models** | Models of user examination behavior | Derive labels from interaction logs |
| **13-month interaction history** | Aggregated click counts per query-document pair | Navboost signal |

### 9.2 User Behavior Improves Ranking

- Incorporating user behavior data can significantly improve ordering of top results
- Large-scale evaluation: 3,000 queries, 12 million user interactions
- Implicit feedback can augment other features, improving ranking accuracy by up to 31% relative to original performance
- Click-based systems serve as implicit human judgments, similar to labeled training data

### 9.3 User Behavior and Ranking Optimization

- Personalized ranking based on inverse reinforcement learning (2024)
- User behavior patterns feed back into ranking models
- Engagement becomes a personalized trust proxy
- Search engines develop brand bias based on prior satisfaction

---

## 10. Personalization

### 10.1 Personalization Signals

| Signal | Description | Influence Level |
|--------|-------------|-----------------|
| **Location** | Biggest source of variation between users' results | Highest |
| **Language/Settings** | Language, region, SafeSearch preferences | High |
| **Device** | Mobile vs. desktop results differ | Medium |
| **Search/Browsing History** | Recent searches and activity shape results | High |
| **Account Signals** | Broader activity when signed in | Medium |
| **Chosen Sources** | User-nominated preferred sources | Growing |

### 10.2 Personalization in AI Search (2026)

- Google's Personal Intelligence in AI Mode connects Gmail, Google Photos, Calendar as retrieval sources
- Available in ~200 countries, 98 languages
- Preferred Sources: users can nominate sites; 345,000+ unique sources selected
- Preferred Source links attract roughly 2× click-through rate
- 9.2% URL overlap across three identical AI Mode runs

### 10.3 Personalization Impact on Ranking

- "The number one ranking" is a fiction—two people entering the same query see different results
- Personalization matters most on ambiguous/short-prefix queries: NDCG@10 improves +8.63% on 1–3 character queries vs. +1.46% on longer queries
- Hybrid embeddings (text + ID-based) enable personalization where lexical matching is least informative
- Personalization accelerates winner-take-most dynamics

### 10.4 Personalization Layers for Marketplace Search

| Layer | Control |
|-------|---------|
| **Identity** | Signed-in accounts, cross-device identity |
| **History** | Long-term browsing and app activity |
| **Short-term session** | Query chains, dwell time, reformulations |
| **Location** | IP, GPS, "near me" inferences |
| **Device** | Hardware, OS, language settings |

---

## 11. Citations and AI Search

### 11.1 Citation in AI Search

- Only 38% of pages cited in Google's AI Overviews also rank in top 10 (down from 76%)
- Ranking position and citation are inversely decoupling
- AI search rewards extractability—clean, self-contained answer fragments
- 89% of citation surface is engine-specific
- 615× citation volume variance between platforms for the same brand

### 11.2 Citation Optimization for Marketplaces

| Strategy | Description |
|----------|-------------|
| **Entity Clarity** | Explicitly define who you are and what you do |
| **Original Proof** | Anchor claims in proprietary data and experience signals |
| **Extractable Answers** | Use structured definitions, comparisons, FAQ schemas |
| **Topic Clusters** | Build coverage that handles multiple inferred intents |
| **E-E-A-T signals** | Editorial ecosystem, expertise, authoritativeness, trustworthiness |

### 11.3 Google's AI Search Guidelines (2026)
- llms.txt files, AI-specific content rewrites, and specialized schema markup are NOT used or rewarded
- Fast, accessible websites with genuine expertise and strong local reputation signals still win
- Editorially supervised AI content improved an average of 8.3 positions
- Unreviewed AI content dropped 12.7 positions

---

## 12. Implications for Business Marketplace Listings

### 12.1 Ranking Architecture for Marketplaces

```
User Query → Retrieval (BM25 + filters) → Candidate Window (100-1000 items)
    → Feature Extraction (query-dependent, document-only, query-only)
    → Learned Ranking Model (LambdaMART / Neural Ranker)
    → Personalization Layer (user context, location, history)
    → Business Rules (monetization, diversity, freshness)
    → Final Ranked Results
```

### 12.2 Key Ranking Factors for Marketplace Listings

| Category | Factors |
|----------|---------|
| **Text Relevance** | BM25 on title, description, category match; phrase-match flags |
| **Quality Signals** | Seller rating, review count, response rate, fulfillment speed |
| **Popularity** | Log of view count, conversion rate, sales velocity |
| **Recency** | Listing age (gaussian decay), inventory freshness |
| **User Behavior** | CTR, dwell time, add-to-cart rate, purchase rate |
| **Personalization** | User's past interactions with similar listings, location, price preference |
| **Business Rules** | Sponsored placements, diversity constraints, category balance |

### 12.3 Optimization Recommendations

1. **Invest in LTR infrastructure:** When ranking signals exceed ~5 interacting factors, manual tuning stops converging
2. **Build feature pipeline:** Ensure training/serving consistency; log features for query-document pairs
3. **Collect judgment data:** Use click models, explicit ratings, and conversion data as relevance labels
4. **Implement two-stage architecture:** Cheap retrieval + expensive reranking to bound latency
5. **Monitor latency:** Keep p99 query latency under 500ms; users abandon after 2.3s
6. **Address cold-start:** Use text embeddings and catalog-quality signals for new listings
7. **Personalize carefully:** Balance personalization with fairness; avoid filter bubbles
8. **Optimize for extractability:** Structure listing data for AI search citation
9. **A/B test continuously:** Divert traffic to measure ranking model impact
10. **Plan for NP-hard limits:** Use greedy algorithms with known approximation bounds; don't chase global optima

---

## 13. Summary Table

| Topic | Key Finding | Source |
|-------|-------------|--------|
| Ranking Methods | Two-stage retrieve-and-rerank is universal; BM25 baseline + ML reranker | Stanford CS276, Google Cloud |
| Algorithms | LambdaMART is production standard; RankNet/LambdaRank pioneered neural LTR | Burges et al., Yahoo! LTR Challenge |
| Relevance | 200+ signals, ~12 carry weight; entity salience and engagement velocity top-tier | Moz 2024, Google 2023 |
| ML | Google transitioned to ML ranking in 2018; daily model rollouts; click-based training data | Google Cloud Blog |
| Bottlenecks | Latency (2.3s abandonment), indexing gates, AI search CTR collapse (61%) | WebPageTest, Pew Research |
| Optimization | Automated ML optimization replaces manual tuning; A/B testing essential | Google Cloud, TechTarget |
| NP-Hard | Novelty/diversity ranking NP-hard; Ulam aggregation hard to approximate | Agrawal et al., Fischer et al. |
| Learning to Rank | Three approaches (pointwise/pairwise/listwise); listwise best for NDCG | Liu T.-Y., Burges et al. |
| User Behavior | Implicit feedback improves ranking by up to 31%; engagement velocity weighted 3.7× | Agichtein et al., Google |
| Personalization | Location is dominant signal; personalization most valuable on short queries | Google, arXiv 2607.13493 |
| Citations | 89% engine-specific; extractability > positional authority; 615× variance | gogochimp, DesignRush |

---

## References

1. Burges, C. et al. (2005). "Learning to Rank using Gradient Descent." RankNet.
2. Burges, C. et al. (2006). "LambdaRank: Learning to Rank with Non-Smooth Cost Functions."
3. Liu, T.-Y. "Learning to Rank for Information Retrieval."
4. Agichtein, E. et al. (2006). "Improving Web Search Ranking by Incorporating User Behavior Information." SIGIR '06.
5. Agrawal, R. et al. (2009). "Diversifying Search Results." WSDM.
6. Clarke, C. et al. (2008). "Novelty and Diversity in Information Retrieval Evaluation." SIGIR.
7. Zhai, C. et al. (2008). "An Exploration of Axiomatic Approaches to Information Retrieval." SIGIR.
8. Fischer, F. et al. (2025). "Ulam Rank Aggregation Is Hard to Approximate for Four Rankings." ESA.
9. Chakraborty, D. et al. (2021). "Approximation Algorithms for Ulam Median." SODA.
10. Google Cloud Blog. "How to provide better search results with AI ranking." 2018.
11. Stanford CS276. "Lecture 14: Learning to Rank." Manning & Nayak.
11. Google. "Search Quality Evaluator Guidelines." 2023.
12. Moz. "2024 Correlation Study."
13. WebPageTest. "Global TTFB Study." April 2024.
14. Pew Research Center. "AI Search Behavior Study." 2025.
15. gogochimp. "Cross-Engine Citation Research." 2026.
16. DesignRush. "AI Overviews Citation Analysis." 2026.
17. Karamiyan, F. et al. (2024). "A personalized ranking method based on inverse reinforcement learning." Engineering Applications of AI.
18. Amazon. "RankFormer: Transformer-based Listwise LTR." 2025.
19. Google. "AI Search Guidelines." May 2026.
20. Google. "Custom Ranking | Programmable Search Engine." Developers Documentation.
