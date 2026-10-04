# Wave 1 Research: NP-Hard Problems in Acquisition Platforms and Marketplaces

**Date:** 2026-10-04
**Scope:** Computational hardness results across 10 core problem domains relevant to acquisition platforms, marketplaces, and due diligence systems.

---

## 1. Problem Classification

| # | Domain | Problem | Hardness Class | Key Reduction Source |
|---|--------|---------|----------------|---------------------|
| 1 | Marketplace Matching | Two-sided assortment optimization (platform design) | NP-hard | — (direct proof) |
| 2 | Marketplace Matching | Fisher market clearing prices (indivisible goods) | NP-hard | — |
| 3 | Marketplace Matching | CEEI (Competitive Equal-Income Equilibrium) | Strongly NP-hard | 3-Partition |
| 4 | Business Valuation | Cardinality-constrained portfolio optimization | NP-hard (MIQP) | — |
| 5 | Business Valuation | Derivative pricing with embedded computation | NP-hard | — |
| 6 | Due Diligence | Optimal fraud rule refinement | NP-hard | — |
| 7 | Due Diligence | Feature scheduling with conflicts | NP-complete | 3-Coloring |
| 8 | Fraud Detection | Dense subgraph detection (fraud rings) | NP-hard | — |
| 9 | Fraud Detection | Optimal rule modification (special cases) | NP-hard | — |
| 10 | Portfolio Optimization | Cardinality-constrained Markowitz | NP-hard | — |
| 11 | Dynamic Pricing | Profit maximization with price memory | NP-hard | Max-3-SAT |
| 12 | Dynamic Pricing | Multi-item pricing with business rules | NP-hard | — |
| 13 | Search Ranking | General ranking/selection optimization | NP-hard | Various |
| 14 | Entity Resolution | Batched entity resolution (optimal batch selection) | NP-hard | Bin Packing / k-way Number Partitioning |
| 15 | Entity Resolution | Minimum queries to discover all matches | NP-hard | — |
| 16 | Recommendation Systems | Engagement-maximizing assignment | NP-hard | — |
| 17 | Auction Design | Optimal multi-item mechanism design | #P-hard | — |
| 18 | Auction Design | Optimal auction (budget-additive bidder) | NP-hard | Partition |
| 19 | Auction Design | Truthful mechanism optimization (interdependent values) | NP-hard | — |
| 20 | Market Efficiency | Collusion detection in repeated games | NP-hard | — |

---

## 2. Complexity Analysis

### 2.1 Marketplace Matching

**Two-Sided Assortment Optimization (Rios & Torrico, 2023):**
- The platform's problem of selecting which suppliers to show each customer is **NP-hard**, even in the simplest case with a time horizon of T=2 periods, one-directional interactions, and sequential matches.
- Common approaches (greedy, myopic) can perform **arbitrarily badly** — no constant-factor approximation without structural assumptions.
- A **constant-factor approximation algorithm** exists under certain platform designs.

**Fisher Markets with Indivisible Goods:**
- Determining whether a competitive equilibrium exists is **NP-hard**, even with three agents having linear utility functions (Devanur et al., 2003).
- The CEEI problem is **strongly NP-hard** in general (strongly NP-hard even for n buyers and 3n goods via 3-Partition reduction).

### 2.2 Business Valuation

**Cardinality-Constrained Portfolio Optimization:**
- The Markowitz mean-variance program with a hard cardinality constraint (K assets out of n) becomes a **Mixed-Integer Quadratic Program (MIQP)**.
- The search space grows combinatorially: O(n choose K) subsets, each requiring continuous weight optimization.
- Even the basic Markowitz problem without cardinality constraints is a convex QP solvable in polynomial time; the cardinality constraint is what introduces NP-hardness.

**Computational Complexity in Financial Products (Arora, Barak, Brunnermeier & Ge):**
- Pricing derivatives can embed NP-hard problems (e.g., densest subgraph detection).
- Information asymmetry arises because sellers can generate instruments whose pricing requires solving NP-hard problems that buyers cannot verify.

### 2.3 Due Diligence

**Fraud Rule Refinement (Rudolf system, VLDB 2016):**
- Computing an optimal set of modifications to fraud detection rules is **NP-hard in general**.
- Even special cases (only new fraudulent transactions, or only new legitimate transactions) remain NP-hard.
- Heuristic algorithms are used to identify the best set of rule modifications.

**Feature Scheduling:**
- Scheduling features into time slots with conflict constraints is **NP-complete** via reduction from 3-Coloring.
- The reduction is an identity mapping: features → vertices, conflicts → edges, slots → colors.

### 2.4 Fraud Detection

**Dense Subgraph Detection:**
- Finding dense subgraphs indicative of fraud rings is **NP-hard** (related to Maximum Clique, Densest k-Subgraph).
- FRAUDAR (Hooi et al., 2016) provides a **near-linear time** algorithm that is camouflage-resistant and provides upper bounds on undetectable fraud.
- Data-dependent bounds on the maximum number of edges fraudulent adversaries can have without detection.

**GNN-Based Fraud Detection:**
- Graph Neural Networks outperform XGBoost by **12–25% AUROC** through relational modeling of fraud rings.
- Production systems achieve <100ms latency at 10K+ TPS with federated learning, yielding 25–45% fraud reduction.

### 2.5 Portfolio Optimization

**Metaheuristics for Rich Portfolio Optimization (Doering et al., 2019):**
- Reviews metaheuristic algorithms (colony optimization, cuckoo search, harmony search, genetic algorithms) for NP-hard portfolio variants.
- Rich constraints (cardinality, transaction costs, leverage limits, factor neutrality) make the problem NP-hard.
- The classical Markowitz problem without such constraints is a convex QP solvable efficiently.

### 2.6 Dynamic Pricing

**Profit Maximization with Memory (Lobo & Boyd, POMS):**
- Formulated as a maximum weighted path on a layered graph.
- **NP-hard** via approximation-preserving reduction from **Max-3-SAT**.
- **No PTAS** exists for any factor better than 7/8.
- Dynamic programming scales **linearly** with time periods T but is **exponential** in model memory (number of past prices affecting demand) and number of items.
- The unconstrained version on a DAG is solvable in O(T·|Q|^p · m) time.

### 2.7 Search Ranking

- Many ranking and selection problems in search platforms reduce to known NP-hard problems (Max-2-SAT, TSP, Knapsack).
- The general pattern: combinatorial explosion of possible rankings, feature assignments, or ad allocations.

### 2.8 Entity Resolution

**Batched Entity Resolution (arXiv 2606.24407):**
- Selecting optimal batches of records to query is **NP-hard** via reduction from **k-way Number Partitioning** (restricted bin packing where all bins must be exactly full).
- Finding the minimum number of queries to discover all match edges is also NP-hard.
- An optimal solution exists under a natural condition on entity sizes.
- Generalizes known hardness results for pairwise ER.

### 2.9 Recommendation Systems

- Recommendation engines reduce to NP-hard optimization problems (assignment, ranking, selection).
- The core issue is combinatorial explosion: millions of users × thousands of items × billions of data points.
- In practice, "97% optimal in 2 seconds" beats "100% optimal in 2 years."

### 2.10 Auction Design

**Optimal Mechanism Design (Deckelbaum & Tzamos, 2012):**
- Computing the revenue-optimal auction in multi-item settings is **#P-hard**, even for a single additive bidder with values independently distributed on two rational numbers.
- NP-hard for a single budget-additive bidder with two possible budget values.
- Myerson's single-item optimal auction is computationally efficient; multi-item generalization is intractable.

**Auctions with Interdependence (arXiv 2603.18668):**
- For n=4 bidders, the (1,β)-Det problem is **NP-hard** for any β>1.
- Query complexity lower bounds: Ω(k^n) queries needed for general case.
- Special cases (n=2, k=2) are tractable with efficient algorithms.

**Algorithmic Information Disclosure (arXiv 2403.08145):**
- Computing the optimal auction in the Bergemann-Pesendorfer model is **NP-hard** via reduction from the Partition problem.
- For unit-demand valuations, optimal pricing is NP-complete if valuation distribution support size ≥ 3.

---

## 3. Current Solutions

| Domain | Solution Approach | Key Techniques | Performance |
|--------|------------------|----------------|-------------|
| Marketplace Matching | Constant-factor approximation | Structural assumptions on platform design | Guaranteed approximation ratio |
| Business Valuation | MIQP solvers | Gurobi, CPLEX, branch-and-bound | Exact for small n; heuristic for large |
| Due Diligence | Heuristic rule refinement | Rudolf system: two heuristics for special cases combined | Near-optimal in practice |
| Fraud Detection | FRAUDAR + GNN | Near-linear time dense subgraph detection; graph neural networks | 12–25% AUROC improvement over XGBoost |
| Portfolio Optimization | Metaheuristics | Genetic algorithms, colony optimization, cuckoo search, harmony search | Good solutions, no guarantees |
| Dynamic Programming | Layered graph DP | DAG shortest path formulation | Linear in T; exponential in memory/items |
| Search Ranking | Learning-to-rank | Gradient boosting, neural ranking models | Production-scale with latency SLAs |
| Entity Resolution | Blocking + clustering | Pairwise classification, cluster-based ER, collective inference | Scalable with quality trade-offs |
| Recommendation Systems | Hybrid ML | Matrix factorization, deep learning, reinforcement learning | 97% optimal in practical time |
| Auction Design | Approximation algorithms | LP relaxations, truthful mechanism design | Constant-factor approximations |

---

## 4. Approximation Algorithms

| Problem | Approximation Ratio | Algorithm | Notes |
|---------|-------------------|-----------|-------|
| Two-sided assortment matching | Constant factor | Structural approximation (Rios & Torrico) | Requires specific platform design assumptions |
| Dynamic pricing (Max-3-SAT reduction) | No PTAS beyond 7/8 | DP on layered graph | Approximation-preserving reduction |
| Fraud rule refinement | Heuristic (no guarantee) | Rudolf: two-phase heuristic | Combines special-case heuristics |
| Portfolio optimization (cardinality) | Heuristic | Greedy screening, Monte Carlo, genetic algorithms | No formal guarantee; empirical evaluation |
| Auction design (multi-item) | Constant factor | LP-based approximations | #P-hard; only approximations tractable |
| Entity resolution (batched) | Optimal under size condition | Pay-as-you-go batching | NP-hard in general; special case tractable |
| Dense subgraph detection | Near-linear time | FRAUDAR | Camouflage-resistant with provable bounds |
| Recommendation assignment | Heuristic | ML-based (deep learning, RL) | No formal guarantee; production-proven |

---

## 5. Heuristics

| Heuristic | Domain | Description | Effectiveness |
|-----------|--------|-------------|---------------|
| Greedy screening | Portfolio optimization | Iteratively add/remove assets based on marginal risk-return contribution | Fast; no optimality guarantee |
| Genetic algorithms | Portfolio optimization | Evolutionary search over asset subsets and weights | Good empirical performance |
| Colony optimization | Portfolio optimization | Ant colony / particle swarm for subset selection | Competitive with GA |
| Cuckoo search | Portfolio optimization | Lévy flight-based metaheuristic | Effective for non-convex landscapes |
| Harmony search | Portfolio optimization | Music-inspired metaheuristic | Good exploration-exploitation balance |
| Rudolf two-phase | Fraud detection | Phase 1: capture missed fraud; Phase 2: remove false positives | Near-optimal in practice |
| FRAUDAR | Fraud detection | Near-linear time dense subgraph detection with camouflage resistance | Provable bounds; real-world validated |
| Blocking + clustering | Entity resolution | Reduce pairwise comparisons via blocking keys; cluster collectively | Scalable; quality depends on blocking |
| Learning-to-rank | Search ranking | Gradient boosted trees, neural rankers | Production-standard; latency-bounded |
| Matrix factorization | Recommendation | SVD, ALS, neural collaborative filtering | Industry-standard; scales to billions |
| Reinforcement learning | Recommendation | Contextual bandits, deep RL | Adapts to dynamic user behavior |
| LP relaxation + rounding | Auction design | Solve LP relaxation; round to feasible mechanism | Constant-factor approximations |
| Myerson-style pricing | Auction design | Single-item optimal; extend heuristically to multi-item | Optimal for single item; heuristic for multi |

---

## 6. ML Approaches

| Approach | Domain | Technique | Key Results |
|----------|--------|-----------|-------------|
| Graph Neural Networks | Fraud detection | GNN-based relational modeling | 12–25% AUROC improvement over XGBoost; 25–45% fraud reduction |
| Reinforcement Learning + GNN | Fraud detection | RL-GNN fusion for real-time detection | Context-aware community mining |
| Deep Learning | Recommendation | Neural collaborative filtering, transformers | Industry-standard at scale |
| Reinforcement Learning | Recommendation | Contextual bandits, policy gradients | Dynamic adaptation to user behavior |
| Learning-to-rank | Search ranking | LambdaMART, neural rankers | Production-deployed with latency SLAs |
| ML for Combinatorial Optimization | General | Learning to make decisions in branch-and-bound, node selection | Promising research direction; replaces handcrafted heuristics |
| Federated Learning | Fraud detection | Privacy-preserving distributed training | Enables cross-institutional fraud detection |
| Collective Entity Resolution | Entity resolution | Probabilistic inference over linked mentions | Handles multi-entity, relational ER |
| Metaheuristic + ML hybrid | Portfolio optimization | ML-guided metaheuristic parameter tuning | Improves convergence and solution quality |

---

## 7. Bottlenecks

| Bottleneck | Domain | Description | Impact |
|------------|--------|-------------|--------|
| Combinatorial explosion | All domains | Search space grows exponentially with problem size | Exact solutions infeasible for large instances |
| No PTAS for dynamic pricing | Dynamic Pricing | Approximation-preserving reduction from Max-3-SAT rules out PTAS beyond 7/8 | Cannot guarantee near-optimal pricing |
| #P-hardness of optimal auctions | Auction Design | Even single-bidder multi-item settings are #P-hard | Optimal mechanism design is fundamentally intractable |
| Information asymmetry | Business Valuation | Sellers can embed NP-hard problems in product pricing | Buyers cannot verify fair pricing; adverse selection |
| Camouflage attacks | Fraud Detection | Fraudsters adapt to detection methods | Arms race; requires continuous model updating |
| Scalability vs. accuracy trade-off | Entity Resolution | Blocking reduces comparisons but loses recall | Quality degradation at scale |
| Latency constraints | Search Ranking, Fraud Detection | Production systems require <100ms response | Limits complexity of models that can be deployed |
| Data sparsity | Recommendation Systems | User-item interaction matrix is extremely sparse | Cold start problem; poor recommendations for new users |
| Adversarial inputs | All domains | Attackers can craft worst-case inputs | Heuristics may fail catastrophically on adversarial instances |
| Lack of formal guarantees | Portfolio Optimization, Recommendations | Metaheuristics and ML provide no optimality bounds | Risk of suboptimal decisions in high-stakes acquisitions |

---

## 8. Citations

1. Rios, I. & Torrico, A. (2023). "Platform Design in Matching Markets: A Two-Sided Assortment Optimization Approach." *arXiv:2308.02584*.
2. Devanur, N.R., Papadimitriou, C.H., Saberi, A. & Vazirani, V.V. (2003). "Market Equilibrium via a Primal-Dual Algorithm for a Convex Program." *JACM*.
3. Chen, X. (2015). "On the Computational Complexity of CEEI." *Working Paper*.
4. Arora, S., Barak, B., Brunnermeier, M. & Ge, R. (2011). "Computational Complexity and Information Asymmetry in Financial Products." *Princeton University*.
5. Gondauri, D. (2026). "P vs NP Problem in Portfolio Optimization: Integrating the Markowitz-CAPM Framework with Cardinality Constraints and Black-Scholes Derivative Pricing." *arXiv:2603.15652*.
6. Doering, J. et al. (2019). "Metaheuristics for Rich Portfolio Optimisation and Risk Management." *Journal of Industrial Engineering International*.
7. Boyd, S. et al. "Convex Optimization Applications." *Stanford University*.
8. Milo, R. et al. (2016). "Rudolf: Interactive Rule Refinement System for Fraud Detection." *VLDB*.
9. Hooi, B. et al. (2016). "FRAUDAR: Bounding Graph Fraud in the Face of Camouflage." *KDD*.
10. "Fraud Detection Using Graph Neural Networks: A Survey." *ACM Digital Library, 2026*.
11. Lobo, D. & Boyd, S. "An Efficient Algorithm for Dynamic Pricing Using a Graphical Representation." *POMS*.
12. Maymin, P.Z. (2026). "Markets are competitive if and only if P ≠ NP." *arXiv:2602.20415*.
13. Deckelbaum, A. & Tzamos, C. (2012). "The Complexity of Optimal Mechanism Design." *arXiv:1211.1703*.
14. "Algorithmic Information Disclosure in Optimal Auctions." (2024). *arXiv:2403.08145*.
15. "Complexity of Auctions with Interdependence." (2026). *arXiv:2603.18668*.
16. "Entity Resolution via Batched Oracle Queries." (2026). *arXiv:2606.24407*.
17. Getoor, L. & Machanavajjhala, A. (2012). "Entity Resolution: Theory, Practice & Open Challenges." *VLDB*.
18. "Machine Learning for Combinatorial Optimization: A Methodological Tour d'Horizon." (2018). *arXiv:1811.06128*.
19. "Why does Netflix need to solve a math problem so hard that no one has proven it's solvable?" *Simple Science Answers*.
20. "Reductions and NP-Completeness — Professional Level." *Senior Stack, 2026*.
21. Erickson, J. "NP-Hard Problems." *University of Illinois Algorithms Textbook*.
22. NIST. "NP-hard." *Dictionary of Algorithms and Data Structures*.
23. Garey, M.R. & Johnson, D.S. (1979). *Computers and Intractability: A Guide to the Theory of NP-Completeness*. W.H. Freeman.
24. Cook, S.A. (1971). "The Complexity of Theorem-Proving Procedures." *STOC*.
25. Karp, R.M. (1972). "Reducibility Among Combinatorial Problems." *Complexity of Computer Computations*.

---

## Summary

This research surveyed NP-hard problems across 10 core domains relevant to acquisition platforms and marketplaces. Key findings:

- **All 10 domains contain NP-hard problems**, confirming that computational intractability is a fundamental challenge in acquisition platform design.
- **Approximation algorithms with provable guarantees** exist for some problems (marketplace matching, dynamic pricing with bounded memory), but many domains rely on heuristics without formal bounds.
- **Machine learning approaches** (GNNs, RL, learning-to-rank) are increasingly used to sidestep combinatorial search, but provide no optimality guarantees.
- **The most fundamental bottlenecks** are combinatorial explosion, adversarial inputs, and the scalability-accuracy trade-off in production systems.
- **Auction design** is the most severely affected domain, with #P-hardness results showing that optimal mechanism design is fundamentally intractable even in simple settings.
