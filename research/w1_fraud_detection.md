# Wave 1 Research: Fraud Detection in Business Marketplaces

**Date:** 2026-10-04
**Focus:** Fraud detection for business marketplaces (M&A platforms, B2B marketplaces, acquisition platforms)
**Method:** 10 web searches, top 3 results each, synthesized

---

## 1. Fraud Types

### 1.1 Marketplace-Specific Fraud Patterns

Business marketplaces face a distinct fraud taxonomy due to their two-sided structure (buyers and sellers transacting through a central platform). The core pattern across all types is **one actor operating many accounts** that appear unrelated.

| Fraud Type | Description | Detection Point |
|---|---|---|
| **Buyer Fraud** | Stolen card purchases, false "item never arrived" claims, friendly fraud/chargeback abuse | Payment & proof of delivery |
| **Seller Fraud** | Fake listings, non-shipment, counterfeit goods, bust-out schemes (build reputation then disappear) | Payout & fulfillment |
| **Triangulation Fraud** | Hidden middleman inserts stolen-card order between real buyer and real retailer; every leg looks legitimate | Cross-account linking |
| **Collusion (Buyer-Seller)** | Same person controls both sides; order is genuine in every database field except no real goods or independent parties | Relationship graph analysis |
| **Account Takeover (ATO)** | Attacker signs into real buyer/seller account and transacts as trusted owner | Continuous authentication |
| **Promotion Abuse** | Bot farms create fake accounts to harvest promotional material; fastest-growing e-commerce fraud threat | Onboarding & behavioral signals |
| **Fake Review Rings** | Clusters of accounts trading with themselves or posting reviews to inflate/bury listings | Graph community detection |
| **Organized Refund/Return Rings** | Return/refund scheme across many accounts funneled to one device, card, or address | Device/network fingerprinting |
| **Synthetic Identity Fraud** | Combination of real and fabricated data to construct fake identity | Identity graph analysis |
| **Transaction Laundering** | Legitimate sales channel used to give appearance of transactions that never made economic sense | Pattern analysis |

### 1.2 M&A Marketplace Fraud Types

For M&A and acquisition platforms specifically, fraud types include:
- **Financial statement fraud** — misrepresentation of target company financials
- **Valuation manipulation** — inflated asset values, hidden liabilities
- **Identity fraud** — fake buyers, sellers, or brokers
- **Collusion between parties** — buyer and seller coordinating to defraud the platform or other parties
- **Money laundering** — using acquisition transactions to legitimize illicit funds
- **Phantom listings** — non-existent businesses or assets listed for sale

### 1.3 Key Insight

The common thread across all marketplace fraud types is **identity misrepresentation**. The platform's core challenge is distinguishing one actor's many accounts from genuine strangers. Device fingerprints, network signals, and behavioral patterns are the linking factors that fraudsters cannot cheaply rotate.

---

## 2. Machine Learning Detection

### 2.1 Supervised Learning (57% of research)

| Technique | Strengths | Typical Performance |
|---|---|---|
| **Random Forest** | Most widely adopted (34 studies); handles tabular data natively; reduces overfitting | >95% accuracy on credit card fraud |
| **XGBoost/LightGBM** | Workhorse for production; trains in minutes on millions of examples; serves inference in 5-15ms; SHAP explanations | AUC 0.94-0.97 on card fraud |
| **SVM** | Effective for linear and non-linear classification via kernels | Good for smaller datasets |
| **Logistic Regression** | Strong baseline; interpretable; fast | Baseline comparator |

### 2.2 Deep Learning

| Architecture | Application | Notes |
|---|---|---|
| **LSTM/RNN** | Sequential transaction data; temporal pattern capture | 8 studies; effective for time-series fraud |
| **CNN** | Structured data treated as grid; hierarchical feature learning | 7 studies |
| **Autoencoders** | Anomaly detection via reconstruction error | Unsupervised; good for novel fraud |
| **GNN (GCN, GraphSAGE, GAT)** | Relational fraud patterns; coordinated fraud rings | GAT: AUC 0.988; BNN: F1 0.890 |
| **Bayesian Neural Networks** | Uncertainty quantification; calibrated risk | Best for minimizing false positives |

### 2.3 Unsupervised & Hybrid Approaches

- **Anomaly detection** — identifies deviations from normal behavior without labeled data
- **Clustering** — surfaces hidden fraud communities
- **Hybrid ensembles** — combine multiple paradigms for robustness
- **Cost-sensitive learning** — penalizes missing fraud more heavily than false alarms

### 2.4 Key Challenges in ML Detection

- **Extreme class imbalance** — fraud often <1% of transactions (sometimes <0.1%)
- **Concept drift** — fraudster tactics evolve continuously, rendering models obsolete
- **Interpretability** — deep learning "black box" problem; regulatory and trust concerns
- **Data privacy** — cross-institutional collaboration limited by confidentiality
- **Label scarcity** — confirmed fraud labels are rare and delayed (chargebacks arrive weeks/months later)

---

## 3. Graph Analysis

### 3.1 Why Graphs Matter

Financial transactions naturally form graph-structured data: accounts as nodes, transactions as edges. Fraudulent behavior often appears as **cycles, dense subgraphs, and anomalous community structures** that are invisible to tabular feature-based models.

### 3.2 Four Fundamental Graph Fraud Patterns

| Pattern | Description | Detection Method |
|---|---|---|
| **Rings & Cycles** | Money laundering, voucher abuse, fake review rings produce cyclic transaction flows | Cycle detection (length 3-5); variable-length path queries |
| **Shared Identifiers** | Synthetic identity fraud: multiple accounts sharing phone, email, device, IP | Group-by-identifier queries; collapse synthetic identities |
| **Proximity to Known Bad Actors** | Risk propagates through graph distance (2-hop default threshold) | Shortest-path scoring; link analysis |
| **Anomalous Community Structure** | Dense subgraphs with high internal volume, low external connectivity | Louvain, Label Propagation, Leiden algorithms |

### 3.3 Graph Algorithms for Fraud Detection

| Algorithm | Fraud Use Case | Complexity |
|---|---|---|
| **PageRank** | Score entities by influence; unusual centrality patterns | O(E) |
| **Betweenness Centrality** | Identify bridge entities used for layering | O(VE) |
| **Louvain/Leiden** | Discover fraud communities and rings | O(n log n) |
| **Label Propagation** | Large-scale community detection for collusion | Near-linear |
| **Node Similarity** | Find accounts with overlapping identifiers | O(n²) |
| **K-Component Detection** | Find strongly connected fraud rings | Polynomial |

### 3.4 Production Architecture

A production graph fraud system spans three layers:
1. **Ingestion** — Kafka/Kinesis → Neo4j; stream transactions, enrich entities
2. **Detection** — Neo4j + GDS + ML; Cypher queries, graph algorithms, feature extraction
3. **Response** — Rules engine + case management; alert generation, automated block/allow

**Batch vs Real-Time:**
- Batch (hourly/daily): Community detection, PageRank, entity resolution
- Real-time (sub-second): Proximity queries, shared identity checks, entity resolution lookups

### 3.5 Graph Performance

A well-tuned graph fraud system typically catches **2-5x more relational fraud** than rules-only systems while maintaining the same false-positive rate. The most significant gains are in synthetic identity detection and collusion rings.

### 3.6 Hard vs Soft Links

- **Hard links** — high-confidence identity relationships (phone, credit card, national ID, bank account)
- **Soft links** — behavioral associations (device fingerprints, cookies, IP addresses)

Super-node transformation: merge hard-link connected components into super-nodes, then reconstruct weighted soft-link graph. This reduced a real-world payment graph from 25M to 7.7M nodes while doubling detection coverage.

---

## 4. Real-Time Scoring

### 4.1 Latency Budgets by Use Case

| Use Case | p99 Latency Budget | Notes |
|---|---|---|
| Card-present (POS) | 100ms | Visa/Mastercard authorization SLA |
| Card-not-present (e-commerce) | 250ms | Checkout conversion drops ~1.5% per 100ms beyond 300ms |
| Account opening | 2s | Allows richer KYC signals |
| Login / ATO prevention | 500ms | Session stays open |
| Authorized push payment | 1s | Banks typically allow 1-2s |
| Telco SIM swap | 3s | User in store/IVR; higher tolerance |

### 4.2 Production Architecture

```
API Gateway → Kafka → Fraud Orchestrator → Feature Store (parallel reads)
→ Rules Engine (1-5ms) → ML Scoring Service (5-15ms) → Decision Thresholds
→ Result → Event Store → Human Review Queue → Analyst Labels → Training Pipeline
```

### 4.3 Decision Outputs

- **Approve** — no friction
- **Step-up** — require additional authentication
- **Decline** — reject transaction

### 4.4 Key Production Considerations

- **Rules engine first** — deterministic signals (blocklist, BIN mismatch, velocity) fire in 1-5ms before ML scoring
- **Feature store** — parallel reads for real-time and batch features
- **Concept drift monitoring** — PSI (Population Stability Index) > 0.2 triggers retraining
- **Training on all labels** — chargeback data alone misses 40-60% of fraud (undisputed drains, SIM swap, friendly fraud)
- **In-memory processing** — delivers high-throughput, low-latency scoring for 100% of transactions

### 4.5 Real-Time Scoring Performance

- LightGBM with proper feature engineering: AUC 0.94-0.97 on card fraud datasets
- SAS Fraud Decisioning: profiles, scores, and evaluates 100% of transactions in real time
- Gradient-boosted trees serve inference in 5-15ms with SHAP explanations

---

## 5. Onboarding Prevention

### 5.1 Why Onboarding Is Critical

Most abuse traces back to accounts that were too easy to open. Layered KYC checks filter out throwaway and synthetic identities before they transact. **The moment of account creation is the highest-leverage intervention point.**

### 5.2 Onboarding Fraud Prevention Techniques

| Technique | Description |
|---|---|
| **Identity Verification (IDV)** | Document verification, biometric authentication, liveness detection |
| **Device Fingerprinting** | 2,200+ digital attributes across phone, email, IP datasets |
| **Phone/Email Validation** | Real-time verification of contact information |
| **Biometric Authentication** | Facial biometrics, deepfake detection, FaceBlock for repeat offenders |
| **Behavioral Risk Signals** | Real-time digital identity and behavioral signals in sign-up flows |
| **KYC/AML Compliance** | Regulatory-compliant identity verification without adding friction |
| **Adaptive Verification Flows** | Risk-based: full IDV for high-risk, lighter checks for low-risk users |

### 5.3 Key Onboarding Metrics

- **6x faster verification times** (Veriff)
- **Up to 2x higher conversion rates** with risk-based flows
- **150ms** decision time for digital identity verification
- **230+ countries** coverage for global onboarding
- **1,000+ real-time risk signals** for fraud prevention

### 5.4 Onboarding Best Practices

1. **Verify identity at onboarding** — layered KYC from email/phone through document verification
2. **Sellers warrant closest scrutiny** — full IDV + proof-of-address for sellers; lighter checks for low-risk buyers
3. **Continuous authentication** — 68% of organizations lack continuous authentication across the user journey
4. **Detect synthetic identities** — combine real and fabricated data detection
5. **Close promo abuse loopholes** — combat multiple account creation for coupon/referral abuse
6. **Calibrate scrutiny to risk** — balance trust and conversion

---

## 6. Bottlenecks

### 6.1 Five Core Bottlenecks in Fraud Detection

| Bottleneck | Description | AI Intervention |
|---|---|---|
| **High False-Positive Rates** | Rule-based systems lack context; analysts waste hours on legitimate activities | Behavioral fraud detection; risk scoring; holistic signal analysis |
| **Slow Detection & Response** | Batch-based monitoring means fraud is reviewed hours after occurrence | Real-time AI transaction monitoring; automated alerts within seconds |
| **Difficulty Detecting New Patterns** | Static rules designed around known scenarios; new attacks walk through | AI anomaly detection; adaptive learning from emerging signals |
| **Scattered Data** | Account, transaction, behavioral, and device data remain siloed | Multi-signal real-time analysis; unified risk picture |
| **Manual Investigations** | High-alert volumes force manual review; backlogs grow | AI triage; automated evidence gathering; prioritized case management |

### 6.2 Economic Impact

- **$5.75** spent on recovery for every **$1** lost to fraud (U.S. financial institutions)
- **44%** of U.S. financial institutions still rely on manual fraud detection
- **42% of issuers** and **26% of acquirers** saved >$5M in fraud attempts over 2 years thanks to AI (Mastercard 2025)
- **75%** of financial institutions expect document forgery to undermine current verification controls within a year

### 6.3 Technical Bottlenecks

- **Extreme class imbalance** — legitimate transactions >99.9% of total
- **Concept drift** — fraud patterns change; models degrade silently
- **Data quality problems** — siloed, incomplete, or inconsistent data
- **Limited model interpretability** — black-box deep learning models
- **High computational costs** — especially for graph algorithms and deep learning
- **Scalability** — graphs with tens of millions of nodes and hundreds of millions of edges
- **Label scarcity** — confirmed fraud labels are rare, delayed, and heterogeneous

---

## 7. Optimization

### 7.1 Feature Selection & Dimensionality Reduction

- **Metaheuristic algorithms** (Kepler Optimization, Ghost Opposition-Based Learning) for feature selection
- **BKOA-GOBL** achieved up to **99.96% accuracy** with **81.82% feature reduction** on fraud benchmarks
- **Random Under-Sampling (RUS)** to mitigate class imbalance; reduces dataset size while preserving minority class signal

### 7.2 Cost-Sensitive Learning

- **Class-weighted learning** — penalizes missing fraud more heavily than false alarms
- **Adaptive threshold optimization** — separates probability estimation from decision policy
- Cost-sensitive RF achieved **94.4% precision, 85.7% recall, 89.8% F1** on credit card fraud
- **Expected misclassification cost** minimization on validation data

### 7.3 Model Optimization Strategies

| Strategy | Approach | Result |
|---|---|---|
| **Ensemble Methods** | RF, GB, hybrid ensembles | Strong performance on tabular data |
| **Sequential DL** | RNN, LSTM for temporal patterns | Captures behavioral sequences |
| **Graph-Based Learning** | GNNs, node2vec, engineered graph features | 2-5x more relational fraud detected |
| **Multimodal Learning** | Combine transaction logs, user behavior, device info | Holistic risk picture |
| **Federated Learning** | Cross-institution collaboration preserving privacy | Addresses data silos |
| **Reinforcement Learning** | Real-time adaptive detection | Context-aware decisions |

### 7.4 Production Optimization

- **Drift monitoring** — PSI thresholds, Prometheus histograms per feature per day
- **Automated retraining** — triggered by drift alerts
- **Lightweight models** — for resource-constrained environments
- **Shared benchmark datasets** — common evaluation protocols
- **Alert triage optimization** — SAS reduced case alert volume by 40%, improved detection rate by 35%, reduced false positives by 18%

---

## 8. NP-Hard Problems

### 8.1 Security Games and Fraud Policing

Fraud policing can be modeled as a **security game** between an administrator and fraudulent users:
- Administrator deploys security resources across locations and levies fines
- Computing the **optimal administrator strategy is NP-hard**
- Greedy algorithm variants achieve at least **half the optimal welfare/revenue**
- **Resource augmentation guarantee**: greedy with one additional resource matches the NP-hard optimal

### 8.2 Computational Complexity in Graph Fraud Detection

| Problem | Complexity | Notes |
|---|---|---|
| Cycle detection (length 3-5) | Polynomial | Neo4j GDS native support |
| Betweenness Centrality | O(VE) | Bridge entity identification |
| Node Similarity | O(n²) | Overlapping identifier detection |
| Community detection (Louvain) | O(n log n) | Scalable to millions of nodes |
| Optimal fraud cluster discovery | NP-hard | Approximation algorithms required |
| Entity resolution at scale | NP-hard | Hard-link super-node transformation reduces complexity |

### 8.3 Detection Limits

- **Fraud type decomposition** — fraud is not homogeneous; each class has distinct observation mechanisms and detection limits
- **Endogenous label corruption** — labels generated through imperfect observation processes
- **Structural non-observability** — some fraud is fundamentally unobservable from available data
- **Feature non-informativeness** — some features carry no signal for certain fraud classes
- **Jensen penalty** — pooling fraud classes with heterogeneous observation rates leads to provable inefficiency

### 8.4 Implications

- Optimal fraud detection is computationally intractable; approximation algorithms are necessary
- Problem decomposition (by fraud type, by observation mechanism) reduces complexity
- Resource augmentation (slightly more budget) can match optimal solutions efficiently
- Near-linear time algorithms exist for homogeneous user types

---

## 9. Adversarial ML

### 9.1 How Fraud Attacks Differ from Standard Adversarial ML

Fraud detection presents **domain-specific challenges** for adversarial attacks:
- Attackers need access to stolen/cloned cards or synthetic identities
- Attackers have access to raw data but not necessarily model features
- Changes in feature space may not correspond to feasible changes in data space
- Attackers aim precisely at the class of interest (targeted attacks)
- Fraud detection is mainly supervised; unsupervised approaches struggle with coverage

### 9.2 Attack Vectors

| Attack Type | Description |
|---|---|
| **Evasion Attacks** | Modify transaction features to avoid detection while maintaining fraud utility |
| **Reinforcement Learning Attacks** | Maximize attacker revenue through RL against fraud detection systems |
| **Feature Space Attacks** | Manipulate raw data to change feature representations |
| **Model Poisoning** | Inject fraudulent patterns into training data |
| **Adversarial Perturbations** | Small, plausibility-bounded changes that degrade model performance |

### 9.3 Defenses

| Defense | Description | Effectiveness |
|---|---|---|
| **Adversarial Training** | Train on adversarially perturbed examples | Recovers substantial lost utility; boosts clean AUC; minimizes expected loss |
| **Robust Feature Engineering** | Features resistant to perturbation | Reduces attack surface |
| **Ensemble Methods** | Multiple models with different vulnerabilities | Harder to attack all simultaneously |
| **Continuous Monitoring** | Detect concept drift and adversarial patterns | Early warning of evolving attacks |
| **Graph-Based Detection** | Relational patterns harder to evade | 2-5x more relational fraud detected |

### 9.4 Adversarial Impact on Financial ML

Small adversarial perturbations (FGSM, PGD with ε=0.05) can materially degrade tabular financial ML models across multiple dimensions:
- **Discrimination** — AUC, KS, Gini degradation
- **Calibration** — ECE, Brier score degradation
- **Economic risk** — Expected Loss, VaR 95, ES 95 degradation
- **Fairness** — disproportionate impact on population groups
- **Explanation stability** — SHAP attributions become unreliable

### 9.5 Key Research Gaps

- Few works on adversarial attacks against fraud detection systems specifically
- Lack of shared datasets due to confidentiality issues
- Synthetic data generators needed for controlled testing
- Connection between adversarial robustness and concept drift underdeveloped
- Multi-agent fraud detection frameworks emerging

---

## 10. Citations

### Foundational Surveys & Reviews

1. **MDPI Applied Sciences (2025)** — "An Introduction to Machine Learning Methods for Fraud Detection" — https://mdpi.com/2076-3417/15/21/11787
2. **MDPI Algorithms (2026)** — "A Survey of Machine Learning and Deep Learning for Financial Fraud Detection: Architectures, Data Modalities, and Real-World Deployment Challenges" — https://mdpi.com/1999-4893/19/5/354
3. **Bonview Press FSI (2024-2025)** — "A Systematic Review of AI-Driven Banking Fraud Detection: Advances, Challenges, and Deployment-Ready Solutions" — https://ojs.bonviewpress.com/index.php/FSI/article/download/8228/2120

### Graph-Based Fraud Detection

4. **GraphWiz** — "Fraud Detection with Graph Databases: Patterns, Algorithms, and Production Architectures" — https://graphwiz.ai/content/graphs/fraud-detection-with-graph-databases
5. **arXiv (2026)** — "Toward Auditable Fraud Detection: Combining Graph Features, Model Explanations, and Agentic Case Investigation" — https://arxiv.org/abs/2607.19266
6. **arXiv (2025)** — "Fraud Detection Through Large-Scale Graph Clustering with Heterogeneous Link Transformation" — https://arxiv.org/html/2512.19061v1

### Deep Learning & Advanced Methods

7. **ACM CSAI (2025)** — "A Comparative Study of Deep Learning and Statistical Models for Fraud Detection" — https://dl.acm.org/doi/full/10.1145/3788149.3788187

### Real-Time Scoring & Production

8. **SAS Fraud Decisioning** — Real-time fraud detection and prevention — https://www.sas.com/en_us/software/fraud-decisioning.html
9. **SAS Fraud Management** — Enterprise fraud management platform — https://www.sas.com/ja_jp/software/fraud-management.html
10. **Abemon** — "Real-Time Fraud Detection Architecture: A Production Guide" — https://abemon.es/en/insights/real-time-fraud-detection-architecture-guide
11. **GitHub Fraud-Guard** — Real-time e-commerce fraud scoring API — https://github.com/kashifftw/Fraud-Guard

### Marketplace Fraud

12. **Shield Labs** — "How to Prevent Marketplace Fraud: Types and Signals" — https://shieldlabs.ai/blog/how-to-prevent-marketplace-fraud
13. **SEON** — "How to Prevent Marketplace Fraud: A Guide for Risk Teams" — https://seon.io/resources/online-marketplace-fraud/
14. **Mercurjs** — "Marketplace Fraud Prevention: How to Stop Buyer Fraud, Seller Fraud, and Collusion" — https://mercurjs.com/marketplace-academy/marketplace-fraud-prevention
15. **Prove** — "How are Marketplaces Affected by Fraud?" — https://www.prove.com/insights/how-are-marketplaces-affected-by-fraud
16. **Veriff for Marketplaces** — AI-powered identity verification and fraud prevention — https://www.veriff.com/industry/marketplaces/veriff-for-marketplaces

### Onboarding Prevention

17. **FraudNet Onboarding** — Enterprise risk management onboarding — https://www.fraud.net/onboarding
18. **Telesign Onboarding** — Safe and simple onboarding fraud prevention — https://www.telesign.com/solutions/onboarding
19. **Veriff New Account Onboarding** — Identity verification during onboarding — https://www.veriff.com/use-cases/new-account-onboarding

### Bottlenecks & Optimization

20. **Excellent WebWorld** — "5 Bottlenecks AI Financial Fraud Detection Can Fix In 2026" — https://excellentwebworld.com/ai-financial-fraud-detection
21. **Frontiers in AI (2025)** — "Tackling fraud detection with an enhanced Kepler optimization and ghost opposition-based learning" — https://frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1710387/pdf
22. **Frontiers in AI (2026)** — "Cost-sensitive random forest with adaptive threshold optimization for imbalanced financial fraud detection" — https://frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2026.1938836/pdf

### NP-Hard Problems & Theory

23. **arXiv (2024)** — "When Simple is Near-Optimal in Security Games" — https://arxiv.org/html/2402.11209v2
24. **AlphaXiv (2026)** — "Fraud Type Decomposition and the Observation-Mechanism Taxonomy: Class-Specific Detection Limits in Payment Networks" — https://alphaxiv.org/abs/2605.31257

### Adversarial ML

25. **ACM Data Economy Workshop** — "Adversarial Learning in Real-World Fraud Detection: Challenges and Perspectives" — https://dl.acm.org/doi/fullHtml/10.1145/3600046.3600051
26. **arXiv (2025)** — "Adversarial Robustness in Financial Machine Learning: Defenses, Economic Impact, and Governance Evidence" — https://arxiv.org/html/2512.15780

---

## Summary Table

| Section | Key Finding | Top Source |
|---|---|---|
| Fraud Types | One actor, many accounts; identity misrepresentation is the core pattern | Shield Labs, SEON, Mercurjs |
| ML Detection | XGBoost/LightGBM workhorse (AUC 0.94-0.97); GNNs for relational fraud | MDPI Survey, ACM CSAI |
| Graph Analysis | 2-5x more relational fraud detected; 4 fundamental patterns | GraphWiz, arXiv 2512.19061 |
| Real-Time Scoring | 100-500ms latency budget; rules engine → ML scoring → decision | SAS, Abemon |
| Onboarding Prevention | Highest-leverage intervention point; layered KYC; risk-based flows | Veriff, Telesign, FraudNet |
| Bottlenecks | False positives, slow response, new patterns, scattered data, manual review | Excellent WebWorld, FSI Review |
| Optimization | Cost-sensitive learning, feature selection (81.82% reduction), drift monitoring | Frontiers in AI |
| NP-Hard Problems | Optimal fraud policing NP-hard; greedy achieves ≥50% optimal | arXiv 2402.11209 |
| Adversarial ML | Evasion attacks; adversarial training recovers utility; tabular vulnerability | ACM DE Workshop, arXiv 2512.15780 |
