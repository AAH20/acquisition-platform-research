# Entity Resolution at Scale for Business Data — Wave 1 Research

**Date:** 2026-10-04  
**Focus:** Entity Resolution  
**Search Queries:** 10 (3 results each, 30 total sources reviewed)

---

## 1. Resolution Methods

Entity resolution (ER) is the process of identifying records across one or more datasets that refer to the same real-world entity and reconciling them into a single canonical representation. The standard ER pipeline consists of five stages:

1. **Normalization / Standardization** — Clean and standardize data (casing, whitespace, phone formats, address tokens, schema names). Studies show standardization alone can improve match recall by 10–20% (Christen, 2012).
2. **Blocking** — Reduce the comparison space from O(N²) to manageable candidate sets by grouping records on shared attributes.
3. **Matching** — Compare candidate pairs field-by-field using similarity functions (exact match, Jaro-Winkler, Levenshtein, Soundex, TF-IDF cosine).
4. **Clustering** — Group matched pairs into entity clusters using connected components or graph algorithms to handle transitivity.
5. **Golden Record Creation (Survivorship)** — Select the best field values from each cluster to produce one canonical record using rules like source priority, most recent, most complete, or matching-based selection.

### Three Core Resolution Approaches

| Approach | Description | Pros | Cons |
|----------|-------------|------|------|
| **Deterministic (Rule-Based)** | Explicit human-defined rules (e.g., "if email matches, same person") | Predictable, explainable, fast, no training data | Brittle, misses fuzzy matches, requires manual maintenance |
| **Probabilistic (Fellegi-Sunter)** | Statistical model computing match likelihood from field agreements/disagreements; rare agreements weighted more | Handles messy data, calibrated confidence, auditable | Harder to explain, requires parameter estimation |
| **ML-Based** | Trained classifier on labeled pairs; captures complex patterns | Highest accuracy in benchmarks, adapts to data | Requires substantial labeled data (1,000+ pairs), less explainable |

**Key Insight:** No single matching algorithm wins everywhere. Production systems should train multiple algorithm families per dataset and use an automatic bake-off to select the winner. Precision and recall need separate fixes — precision requires hard rule-based vetoes; recall requires more diverse candidate retrieval.

---

## 2. Machine Learning for Entity Resolution

### Deep Learning Methods

- **DeepER** and **DeepMatcher** are two major deep-learning-based ER solutions. DeepER uses recursive neural networks over structured records; DeepMatcher uses pre-trained language models for sequence matching.
- **Magellan** is an end-to-end ER framework using classical ML (random forests, SVMs, logistic regression) that serves as a baseline for deep learning comparisons.
- Deep learning approaches mitigate the need for dataset-specific feature engineering by constructing distributed representations of entity records.
- **Transformer-based models** can capture semantic similarities that string-based methods miss (e.g., "IBM" = "International Business Machines").

### Transfer Learning + Active Learning

- Kasai et al. (ACL 2019) proposed combining transfer learning with active learning for low-resource deep ER. The method learns a transferable model from a high-resource setting, then fine-tunes with a few actively-selected informative examples.
- Achieves comparable or better performance than state-of-the-art while using **an order of magnitude fewer labels**.

### LLM-Based Resolution

- LLMs exhibit significantly greater robustness and generalization to unseen entities not in training or demonstration sets.
- A 2026 comprehensive survey (Karapiperis et al., ACM Computing Surveys) categorizes DL techniques by learning paradigms across the canonical blocking and matching pipeline.
- **LLM-as-judge cascade pattern:** Stage 1 scores candidate pairs with sentence embeddings (cosine similarity); Stage 2 sends only the ambiguous band (5–15% of candidates) to an LLM for binary SAME/DIFFERENT judgment with structured prompts.
- Batching LLM adjudication (presenting entire clusters rather than pairwise) cuts LLM calls by 60–80%.

### Bayesian Approaches

- The CHOMPER model (2026) generalizes probabilistic ER using a mixture of exponential family distributions, accommodating "multiple truths" — variables whose observations may have multiple true values across databases.
- Supports MCMC and variational inference for massive datasets.

---

## 3. Graph Methods

### Graph-Based ER Architecture

- **Nodes** = records; **Edges** = pairwise match decisions with confidence scores.
- **Connected components** form entity clusters, capturing transitive relationships: if A matches B and B matches C, then {A, B, C} form one entity even if A and C never directly matched.
- **Transitive closure** is the mechanism that transforms pairwise linkage into entity resolution.

### Graph Neural Networks for ER

- **HierGAT (Hierarchical Graph Attention Networks, SIGMOD 2022):** Models interdependence between different ER decisions using graph attention. Identifies discriminative words from attributes and finds joint ER decisions rather than independent pairwise classification.
- **Graph embedding techniques** combined with link prediction improve ER quality in graph databases (Mekki et al., 2022).
- **Unsupervised graph-based ER** for complex entities uses community detection and graph clustering.

### GraphRAG Entity Resolution

- In GraphRAG systems, unresolved duplicates inflate node counts by 20–40%, degrading community detection and multi-hop retrieval.
- **Cascade pattern:** Deterministic identifier rules → string blocking → embedding triage → LLM adjudication.
- **Incremental resolution:** Block new entities against existing canonical index; only resolve new-to-new within batch. Cuts compute by 80–95% in steady state.
- **Merge provenance** stored as graph metadata enables un-merging bad decisions.

### Risk: Error Propagation

- A single false-positive link can chain hundreds of records together through transitive closure.
- Mitigation: cluster-level validation rules (maximum cluster size, minimum intra-cluster similarity thresholds, flagging low-confidence constituent links).

---

## 4. Bottlenecks

### Computational Complexity

- **Quadratic search space:** N records require N×(N−1)/2 comparisons — 500 billion for 1M records. This is the fundamental scalability bottleneck.
- **O(|R| × |S|)** search space is computationally infeasible for large datasets.

### Label Scarcity

- ML-based ER typically requires 1,000+ labeled pairs, which are unavailable in realistic applications.
- Active learning candidate pool creation is itself a bottleneck — most candidate pairs are "easy" negatives providing little informational value.

### Deep Learning Cost

- Transformer-based models introduce high computational cost bottlenecks.
- ALER system addresses this with frozen bi-encoder architecture generating static embeddings once, then iteratively training a lightweight classifier — achieving 3× speedup and 3.8× latency reduction.

### Memory Constraints

- Dedupe library fails to scale beyond 2 million records due to memory constraints.
- MERAI pipeline successfully processed up to 15.7 million records.

### Data Quality

- Customer data degrades at 25–30% per year.
- Typical B2B database has 10–30% duplicate records.
- Poor data quality costs organizations an average of $12.9 million/year (Gartner).

### Transitive Closure Risk

- One false-positive link can silently merge unrelated entities, chaining hundreds of records.
- Every cross-group merge must be actively re-verified.

---

## 5. Optimization

### Blocking Optimization

- Good blocking reduces candidate pair count by **99% or more** with modest recall loss.
- **Multi-signal blocking:** Combine normalized string key + entity-type constraint + token-overlap floor (Jaccard > 0.3).
- **Hybrid candidate generation:** Union of string blocking and embedding nearest-neighbor search recovers missed pairs.
- **Semantic-aware blocking** (Wang et al., ICDE 2016): Uses LSH to unify textual and semantic features, considerably improving blocking quality.

### Cascade Architecture

- **Deterministic identifier rules** (cheapest, most reliable) → **String blocking** (candidate generation) → **Embedding scoring** (triage) → **LLM adjudication** (ambiguous residue only).
- Teams running LLM adjudication on everything pay 5–20× more for marginal precision gains.
- Teams relying on embeddings alone plateau around 80–90% merge precision.

### Incremental Processing

- Block new entities against existing canonical entity index.
- Only resolve new-to-new among the batch.
- Cuts resolution compute by **80–95%** versus full re-resolution.

### Caching

- Content-hash cache on (mention_a, mention_b, context) means re-indexing costs 10–20% of original adjudication cost.

### Cost Optimization

- For 100k-entity corpus: embedding scoring ~$10–100; LLM adjudication of ambiguous band ~$50–2,000.
- Batching and caching cut adjudication costs by 60–80%.
- Engineering time (building cascade, gold set, provenance store): 2–6 engineer-weeks.

### Algorithm Selection

- Train several algorithm families per dataset; use automatic bake-off to pick winner.
- No single matching algorithm wins everywhere.

---

## 6. NP-Hard Problems

### Batched Entity Resolution

- **Formal problem:** Selecting optimal batches to submit to a bounded-size oracle that clusters records within each batch.
- **Proved NP-hard** in general (pERbacco paper, 2026).
- **Polynomial-time optimal solution** exists when entity sizes obey a natural regularity condition.
- **pERbacco algorithm:** Approximate batch-selection strategy maximizing newly discovered matches per oracle invocation.
- Pay-as-you-go property: practitioners stop querying once target recall is reached.

### Knowledge Pattern Evaluation

- The evaluation problem for knowledge patterns is **NP-complete** with respect to combined complexity.
- However, it is in **P time** with respect to data complexity.
- The containment problem for knowledge patterns is also **NP-complete**.

### Implications

- Optimal batch selection, knowledge pattern evaluation, and containment are fundamentally hard problems.
- Practical systems rely on approximation algorithms, greedy heuristics, and regularity conditions for tractability.

---

## 7. Deduplication

### Definition

Deduplication applies record linkage reasoning within a single dataset — finding records that describe the same entity and merging them. It is a subset of entity resolution focused on single-collection cleanup.

### Distinction from ER

| Aspect | Deduplication | Entity Resolution |
|--------|--------------|-------------------|
| Scope | Single dataset | Cross-dataset + clustering + canonicalization |
| Output | Deduplicated dataset with merged records | Entity clusters and golden records |
| Techniques | Matching + merge/purge survivorship rules | Matching + graph clustering + canonicalization |

### Merge/Purge

- Hernández and Stolfo (1995) formalized merge-purge for deduplication.
- Survivorship rules determine which source values populate the golden record.

### Enterprise Scale

- MERAI pipeline: 15.7 million records processed with higher F1 than Dedupe and Splink.
- Dedupe library: fails beyond 2M records (memory constraints).
- Splink: scales to 100M+ using Spark/DuckDB.

---

## 8. Record Linkage

### Definition and History

Record linkage is the process of identifying, linking, and merging records from disparate datasets that refer to the same real-world entity. Originated in 1946 with Halbert Dunn's vital statistics work; formalized by Fellegi-Sunter (1969).

### Fellegi-Sunter Model

The classical probabilistic foundation:
- **m-probability:** P(field agreement | true match)
- **u-probability:** P(field agreement | non-match, by chance)
- **Match weight:** log(m/u) for agreements; log((1−m)/(1−u)) for disagreements
- Composite score classifies pairs as match / non-match / clerical review
- Can be estimated unsupervised via Expectation-Maximization

### Pipeline

1. Schema harmonization
2. Data standardization
3. Blocking
4. Pairwise comparison
5. Classification (deterministic, probabilistic, or ML)
6. Transitive closure → entity resolution

### Privacy-Preserving Record Linkage (PPRL)

- **Bloom filter encoding:** Converts field values into binary vectors preserving approximate similarity but irreversible.
- **Secure multi-party computation (SMPC):** Computes match scores on encrypted data.
- **Trusted third-party models:** Route encrypted records through neutral intermediary.

### Transitive Closure

- Connects records never directly compared: A↔B and B↔C implies A↔C.
- Risk: error propagation through false-positive links.
- Mitigation: cluster-level validation, maximum cluster size, minimum similarity thresholds.

---

## 9. Blocking

### Purpose

Blocking reduces the quadratic comparison space by partitioning records into groups (blocks) using cheap keys. Only records within the same block are compared.

### Two Paradigms

1. **Blocking workflows:** Extract signatures from every entity profile; cluster entities with identical/similar signatures into blocks. Every pair in a block is a candidate.
2. **Nearest-neighbor methods:** Convert all profiles to vectors; identify closest ones to every query. No redundant candidates.

### Blocking Techniques

| Technique | Description |
|-----------|-------------|
| **Standard Blocking** | Tokenize attribute values on whitespace; each token is a block key |
| **Q-Grams Blocking** | Use q-gram substrings as signatures |
| **Sorted Neighborhood** | Sort records by key; compare within sliding window |
| **Canopy Clustering** | Overlapping clusters using loose/tight thresholds |
| **LSH (Locality-Sensitive Hashing)** | Probabilistic hashing for approximate nearest neighbors |
| **Semantic-Aware Blocking** | LSH over combined textual + semantic features |
| **CER-Blocking** | Inverted index over RDF triples for Semantic Web |

### Block Cleaning

- **Redundant candidates:** Repeated across overlapping blocks.
- **Superfluous candidates:** Non-matching entities within blocks.
- Block cleaning and comparison cleaning restructure blocks based on global patterns to eliminate both types.

### Trade-offs

- Aggressive blocking trades recall for cost.
- Token-based blocking misses pairs with no shared tokens (e.g., "IBM" vs "International Business Machines").
- Hybrid approach: union string blocking + embedding NN search.

### Performance

- Good blocking reduces candidates by **99%+** with modest recall loss.
- Multi-pass blocking with different keys catches matches any single strategy would miss.

---

## 10. Active Learning

### Motivation

ML-based ER requires large labeled datasets that are typically unavailable. Active learning selects the most informative pairs for human labeling, reducing annotation effort by an order of magnitude.

### Key Approaches

1. **Transfer + Active Learning (Kasai et al., ACL 2019):**
   - Learn transferable model from high-resource dataset.
   - Fine-tune with actively-selected informative examples from target dataset.
   - Order-of-magnitude fewer labels than pure supervised learning.

2. **ALER (Active Learning for Entity Resolution, 2026):**
   - Semi-supervised pipeline with frozen bi-encoder generating static embeddings once.
   - Iteratively trains lightweight classifier on actively-acquired labels.
   - HNSW index for O(log n) query resolution.
   - 3× speedup, 3.8× latency reduction vs. fastest baseline.
   - 20× speedup in resolution latency on large-scale benchmarks.

3. **Candidate Pool Strategy:**
   - Most candidate pairs are "easy" negatives with little informational value.
   - Active selection focuses on ambiguous pairs near decision boundary.
   - Small representative random sampling for initial pool.

### AL System Bottlenecks

- Traditional AL systems computationally expensive, designed for traditional classifiers and lexical features.
- Modern deep methods with Transformers introduce high computational cost.
- ALER solves this with frozen embeddings + lightweight classifier.

### Pay-As-You-Go

- Batched oracle queries with explicit budget control.
- Recall improves at each step; stop when target recall reached.
- NP-hard in general; optimal under entity-size regularity condition.

---

## 11. Citations

1. Agarwal, A., Singh, S., & Chaurasiya, V.K. (2022). "Assessing Entity Resolution techniques based on deep learning." *IEEE 3rd Global Conference for Advancement in Technology (GCAT)*. DOI: 10.1109/GCAT55367.2022.9971860

2. Augsten, N. & Nejdl, W. (2022). "How to reduce the search space of Entity Resolution: with Blocking or Nearest Neighbor?" *arXiv:2202.12521*.

3. Benjelloun, O., Garcia-Molina, H., Menestrina, D., Su, Q., Whang, S.E., & Widom, J. (2009). "Swoosh: A Generic Approach to Entity Resolution." *The VLDB Journal*, 18(1), 255–276.

4. Christen, P. (2012). *Data Matching*. Springer.

5. Fellegi, I.P. & Sunter, A.B. (1969). "A Theory for Record Linkage." *Journal of the American Statistical Association*, 64(328), 1183–1210.

6. Hernández, M.A. & Stolfo, S.J. (1995). "The Merge/Purge Problem for Large Databases." *SIGMOD*.

7. Karapiperis, D., Tjortjis, C., & Verykios, V. (2026). "A Comprehensive Survey of Deep Learning for Entity Resolution." *ACM Computing Surveys*, 58(14), Article 366. DOI: 10.1145/3828660

8. Kasai, J., Qian, K., Gurajada, S., Li, Y., & Popa, L. (2019). "Low-resource Deep Entity Resolution with Transfer and Active Learning." *Proceedings of ACL 2019*, 5851–5861. DOI: 10.18653/v1/P19-1586

9. Kobayashi, F. & Talburt, J. (2018). "Machine Learning Comparison in Entity Resolution." *IEEE International Conference on Computational Science and Computational Intelligence (CSCI)*, 239–244. DOI: 10.1109/CSCI46756.2018.00052

10. Mekki, N. et al. (2022). "Entity Resolution in graph databases: comparison study." *IEEE*.

11. Papadakis, G., Skoutas, D., Thanos, E., & Palpanas, T. (2020). "A Survey of Blocking and Filtering Techniques for Entity Resolution." *ACM*.

12. Wang, Q., Cui, M., & Liang, H. (2016). "Semantic-aware blocking for entity resolution." *IEEE 32nd International Conference on Data Engineering (ICDE)*, 1468–1469. DOI: 10.1109/ICDE.2016.7498378

13. Costa, G.D.A. & De Oliveira, J.M.P. (2016). "A Blocking Scheme for Entity Resolution in the Semantic Web." *IEEE 30th International Conference on Advanced Information Networking and Applications (AINA)*, 1138–1145. DOI: 10.1109/AINA.2016.23

14. "Entity Resolution via Batched Oracle Queries" (2026). *pERbacco: NP-hardness and optimal batch selection*. Pith Science.

15. "A theoretical framework for knowledge-based entity resolution" (2014). *Theoretical Computer Science*. DOI: 10.1016/j.tcs.2014.06.030

16. "ALER: An Active Learning Hybrid System for Efficient Entity Resolution" (2026). *arXiv:2601.20664v1*.

17. "Entity Resolution in Practice: Lessons from a Self-Serve Pipeline" (2026). *arXiv:2607.26298v1*.

18. "A Comprehensive Bayesian Approach to Entity Resolution" (2026). *CHOMPER model*. *arXiv:2608.20601*.

19. "A Robust and Efficient Pipeline for Enterprise-Level Large-Scale Entity Resolution" (2025). *MERAI*. *IEEE BigData 2025*, 2359–2368. DOI: 10.1109/BigData66926.2025.11400814

20. "Entity Resolution with Hierarchical Graph Attention Networks" (2022). *HierGAT*. *SIGMOD '22*, 429–442. DOI: 10.1145/3514221.3517872

21. Dunn, H.L. (1946). "Record Linkage." *American Journal of Public Health*, 36(12), 1412–1416.

22. Dong, X., Halevy, A., & Madhavan, J. (2005). "Reference reconciliation in complex information spaces." *SIGMOD*.

23. "What Is Entity Resolution? A Complete Guide for Data Engineers" (2026). Kanoniv.

24. "Entity Resolution: The Definitive Guide" (2026). MatchLogic.

25. "What Is Entity Resolution? A Practical Guide for AI, KYC and Customer 360" (2026). Tilores.

26. "What are the best GraphRAG entity resolution optimization techniques?" (2026). Indexical.dev.

27. "Entity Optimization in 2026" (2026). Prompt&Co Research.

28. Stanford Entity Resolution Framework (SERF). *http://infolab.stanford.edu/serf*

29. "(Almost) all of entity resolution" (2024). *PMC11636688*.

30. Grokipedia. "Record linkage." https://grokipedia.com/page/Record_linkage

---

## Summary Table

| Section | Key Finding | Top Methods | Primary Bottleneck |
|---------|-------------|-------------|-------------------|
| **Resolution Methods** | 5-stage pipeline: normalize → block → match → cluster → golden record | Deterministic, Probabilistic (F-S), ML/DL | No single winner; dataset-specific |
| **Machine Learning** | DL captures semantic similarity; LLMs generalize to unseen entities | DeepER, DeepMatcher, HierGAT, LLM-as-judge | Label scarcity (1,000+ pairs needed) |
| **Graph Methods** | Connected components + GNN for joint decisions | HierGAT, graph embeddings, community detection | Error propagation via transitive closure |
| **Bottlenecks** | O(N²) search space; label scarcity; memory; data degradation | MERAI (15.7M records), ALER (frozen embeddings) | Quadratic complexity is fundamental |
| **Optimization** | Cascade: rules → blocking → embeddings → LLM; incremental; caching | Multi-signal blocking, batching, HNSW index | Engineering time (2–6 weeks) |
| **NP-Hard Problems** | Optimal batch selection NP-hard; knowledge pattern evaluation NP-complete | pERbacco approximation; regularity conditions | No polynomial-time general solution |
| **Deduplication** | Single-dataset merge/purge; subset of ER | Dedupe, Splink, MERAI | Memory limits (Dedupe < 2M records) |
| **Record Linkage** | Fellegi-Sunter probabilistic model; PPRL for privacy | Deterministic, probabilistic, ML classification | Transitive closure error propagation |
| **Blocking** | Reduces candidates by 99%+; two paradigms (blocking workflows, NN) | Standard, Q-Grams, LSH, Semantic-aware, CER | Recall/cost trade-off; misses non-token matches |
| **Active Learning** | Order-of-magnitude label reduction; transfer + AL | Kasai et al. (ACL 2019), ALER (2026) | Candidate pool creation; easy negatives dominate |

---

*Research completed: 10 web searches, 30 sources reviewed, 11 sections synthesized.*
