# Wave 3: Cross-Cutting NP-Hard Problems in Dual-Use Technology Acquisitions

**Research Focus:** Computational hardness across defense acquisition, technology transfer, portfolio optimization, cross-border M&A, due diligence, valuation, matching, auctions, entity resolution, and search ranking.

**Date:** 2026-10-05

---

## Executive Summary

NP-hard problems permeate every stage of dual-use technology acquisition pipelines. From target identification and due diligence to portfolio selection, auction design, entity resolution, and search ranking, the underlying combinatorial optimization problems are computationally intractable in the worst case. This document synthesizes findings from 10 research domains, classifying problems by complexity, cataloging current solution approaches, and identifying bottlenecks relevant to building an acquisition platform.

---

## 1. Problem Classification

### 1.1 Core NP-Hard Problem Classes in Acquisitions

| Domain | Problem | Complexity Class | Source |
|--------|---------|-----------------|--------|
| Defense Acquisition | Defender-Attacker (-Defender) Optimization | Bilevel NP-hard | Brown et al. (NPS) |
| Defense Acquisition | Network Resource Allocation (Shared Defense) | NP-hard (Σ₂-complete for defensive domination) | AAAI 2007; Arxiv 2504.14390 |
| Defense Acquisition | Stackelberg Security Games (General Thresholds) | NP-hard (mixed strategy) | IJCAI 2022 |
| Technology Transfer | Knapsack / Subset Selection | Weakly NP-hard | Garey & Johnson 1979 |
| Portfolio Optimization | Cardinality-Constrained Markowitz (MIQP) | NP-hard (strongly NP-hard with transaction costs) | Bienstock 1996; Arxiv 2603.15652 |
| Portfolio Optimization | Index Tracking with K-sparsity | NP-hard (Ising ground state) | Arxiv 2601.07792 |
| Cross-Border M&A | Information Asymmetry Reduction | NP-hard (contracting cost optimization) | Wiley 2010 |
| Due Diligence | Multi-dimensional Target Screening | NP-hard (set cover / maximum coverage) | Preprints 202509.2038 |
| Valuation | Network Defense Pricing (DBR) | NP-hard (reduction from Vertex Cover) | Arxiv 2404.11545 |
| Matching | Matching Interdiction | Strongly NP-complete | Arxiv 0804.3583 |
| Matching | Defensive Dominating Set | Σ₂-complete | Arxiv 2504.14390 |
| Auctions | Winner Determination (Combinatorial) | NP-complete (reduction from Set Packing) | Sandholm et al. (CMU) |
| Auctions | VCG False-Name Manipulation | NP-hard | Parkes (Harvard) |
| Entity Resolution | Optimal Batch Selection | NP-hard | Pith Science 2606.24407 |
| Search Ranking | Adversarial Ranking Manipulation | Game-theoretic (IRPD) | Arxiv 2501.00745 |

### 1.2 Complexity Hierarchy

```
P ⊆ NP ⊆ NP-complete ⊆ NP-hard ⊆ PSPACE
                    ↑
         Most acquisition problems
         reside here (optimization
         versions of NP-complete
         decision problems)
```

- **Weakly NP-hard:** Knapsack, Subset-Sum — admit pseudo-polynomial algorithms (O(n·W) DP)
- **Strongly NP-hard:** TSP, 3-Partition, Matching Interdiction — no pseudo-polynomial algorithm exists unless P=NP
- **Σ₂-complete:** Defensive Dominating Set — harder than NP, requires alternating quantifiers
- **Bilevel NP-hard:** Defender-Attacker optimization — nested optimization (min-max)

---

## 2. Complexity Analysis

### 2.1 Portfolio Optimization with Cardinality Constraints

The classical Markowitz mean-variance problem is a convex QP solvable in polynomial time. Adding a cardinality constraint |supp(w)| ≤ K transforms it into a **mixed-integer quadratic program (MIQP)**:

- **Search space:** C(n,K) combinations (e.g., C(100,30) ≈ 3×10²⁵)
- **Decision version:** Given Σ, μ, V*, R*, K, does there exist w with wᵀΣw ≤ V*, μᵀw ≥ R*, |supp(w)| ≤ K?
- **NP-hardness proof:** Reduction from best-subset selection (Bertsimas et al. 2016)
- **Ising mapping:** Binary PO formulation maps to Ising Hamiltonian; ground state is NP-complete (Sherrington & Kirkpatrick 1975; Lucas 2014)
- **With transaction costs:** Becomes MINLP, strongly NP-hard (Moehle et al. 2021)

### 2.2 Combinatorial Auction Winner Determination

The Winner Determination Problem (WDP) in combinatorial auctions:

- **WDP-OR:** NP-complete even with unit bids, single bid per bidder, items in ≤2 bids (reduction from Stable Set)
- **WDP-XOR:** NP-complete even with adjacent items (reduction from Job Interval Selection)
- **With budget constraints:** NP-hard even with 2 bidders (Lehmann et al. 2003)
- **Approximability:** O(m^(1-ε)/(k+1)) is NP-hard unless NP=ZPP

### 2.3 Network Defense Resource Allocation

The general network defending problem with shared resources:

- **Single Threshold Model:** O(n^ω log n) — polynomial (LP-based)
- **Isolated Model:** O(mn log n) — polynomial (max-flow based)
- **General Model:** NP-hard (reduction from MAX-DNF)
- **Inapproximability:** No polynomial-time approximation algorithm exists unless P=NP (for damage minimization variant)
- **Tight approximation:** 2-approximation via LP-rounding (integrality gap = 2)

### 2.4 Matching Interdiction

Given a graph with edge weights and interdiction costs:

- **NP-complete** even on graphs of isolated edges (reduction from Knapsack)
- **Strongly NP-complete** on simple bipartite graphs with unit weights/costs
- **Pseudo-polynomial algorithm** exists for bounded treewidth graphs
- **Min-max nature** requires adapting standard treewidth DP approaches

### 2.5 Entity Resolution via Batched Oracle Queries

- **Optimal batch selection:** NP-hard in general
- **Polynomial-time optimal:** Exists under regularity condition on entity sizes
- **Practical algorithm:** pERbacco (approximate batch selection)
- **Pay-as-you-go:** Incremental recall with controlled oracle consult costs

### 2.6 Stackelberg Security Games with General Thresholds

- **Uniform thresholds:** Optimal mixed strategy computable efficiently (compact representation)
- **General thresholds:** Computing optimal mixed strategy is NP-hard
- **Fractional vs. Mixed:** OPT_m(R) ≥ OPT_f(R); gap bounded by θ_max/R
- **Patching algorithm:** Polynomial-time close-to-optimal with O(n²) pure strategies

---

## 3. Current Solutions

### 3.1 Exact Methods

| Method | Applicability | Limitation |
|--------|--------------|------------|
| ILP/MIP Solvers (Gurobi, CPLEX) | Small-to-medium instances (n ≤ 30-40) | Exponential worst-case |
| SAT/SMT Solvers (Z3, CaDiCaL) | Decision problems, verification | No optimization |
| CP-SAT (OR-Tools) | Scheduling, packing | Limited to specific structures |
| Branch-and-Bound | Structured instances | Requires good bounds |
| Dynamic Programming | Weakly NP-hard with small numbers | Pseudo-polynomial only |

### 3.2 Decomposition Approaches

- **Benders Decomposition:** DHS-MXM-DECOMP for defender-attacker problems (iterative cut generation)
- **Column Generation:** For large-scale LPs in security games
- **Dantzig-Wolfe:** For structured integer programs

### 3.3 Special Case Algorithms

- **Bounded Treewidth:** Pseudo-polynomial algorithms for matching interdiction
- **Interval Graphs:** Polynomial-time for defensive dominating multiset
- **Trees, Cycles, Cliques:** Polynomial-time for defensive domination
- **Single-index covariance:** Simplified portfolio optimization

---

## 4. Approximation Algorithms

### 4.1 Guaranteed Approximation Ratios

| Problem | Approximation Ratio | Algorithm | Source |
|---------|-------------------|-----------|--------|
| Network Defense (shared resources) | 2-approximation | LP-rounding | AAAI 2007 |
| TSP (metric) | 1.5-approximation | Christofides | Christofides 1976 |
| Set Cover | H(d) ≈ ln(d) | Greedy | Johnson 1974 |
| Knapsack | FPTAS | DP-based | Ibarra & Kim 1975 |
| General Combinatorial Auctions | Polynomially-bounded | Nisan 2003 | Nisan 2003 |
| Security Games (general thresholds) | Close-to-optimal | Patching algorithm | IJCAI 2022 |

### 4.2 Inapproximability Results

- **Network Defense (damage minimization):** No polynomial-time approximation algorithm exists unless P=NP
- **WDP:** Approximating within O(m^(1-ε)/(k+1)) is NP-hard unless NP=ZPP
- **MAX-DNF:** No constant-factor approximation unless P=NP

### 4.3 LP Relaxation Quality

- **Integrality gap of 2** for network defense LP relaxation (tight)
- **Fractional strategies** provide lower bounds for mixed strategies in security games
- **Convexity of OPT_f(·)** enables bounding techniques

---

## 5. Heuristics

### 5.1 Greedy Approaches

- **Greedy screening** for portfolio selection (top-K by Sharpe ratio)
- **Greedy set cover** for sensor/test placement
- **Greedy batch selection** for entity resolution (baseline for pERbacco)

### 5.2 Metaheuristics

| Heuristic | Application | Performance |
|-----------|-------------|-------------|
| Genetic Algorithms | Portfolio optimization | Competitive with MIQP for large n |
| Simulated Annealing | Combinatorial auctions | Good empirical performance |
| Tabu Search | Matching problems | Escapes local minima |
| Variational Neural Annealing | Portfolio optimization (Ising) | GPU-accelerated sampling |
| Energy-Based Models (THRML) | Index tracking | 4.31% tracking error vs 5.66-6.30% baselines |

### 5.3 Problem-Specific Heuristics

- **Patching Algorithm:** Iteratively adds pure strategies to patch poorly defended targets (security games)
- **Canonical Transformation:** Reallocates resources without decreasing defending power (network defense)
- **Monte Carlo Sampling:** Over K-subsets for portfolio evaluation
- **Delta-based Linearization:** For derivative-augmented portfolio optimization

---

## 6. Machine Learning Approaches

### 6.1 Reinforcement Learning

- **RL-guided combinatorial auctions:** CAFormer (differentiable Transformer) for cyber defense resource allocation
- **Q-value-derived valuations:** Host-specific defensive action bundles from RL agents
- **Adversarial regret minimization:** Learning incentive-compatible mechanisms
- **CAGE Challenge 2:** DARPA cyber defense simulation environment

### 6.2 LLM-Based Reasoning

- **Graph-R1:** NP-hard graph problems as synthetic training corpus for LLM reasoning
- **Long CoT SFT:** Rejection-sampled NPH instances for reasoning depth
- **RL with fine-grained rewards:** Sharpens reasoning efficiency
- **EHOP Dataset:** Everyday Hard Optimization Problems for testing reasoning vs. recitation

### 6.3 Neural Approximation

- **Variational Neural Annealing (VNA):** For large-scale portfolio optimization
- **Energy-Based Models:** Boltzmann sampling over high-quality portfolios
- **Neural Auction Mechanisms:** CAFormer for differentiable mechanism design
- **Graph Neural Networks:** For entity resolution and matching

### 6.4 ML for Entity Resolution

- **pERbacco:** Approximate batch selection algorithm
- **Recall-per-oracle-call:** Optimized batch selection under budget constraints
- **Six datasets evaluated:** Superior to state-of-the-art baselines

---

## 7. Bottlenecks

### 7.1 Computational Bottlenecks

1. **Exponential search spaces:** C(n,K) for portfolio selection, 2^k for auction winner determination
2. **Bilevel structure:** Defender-attacker problems require nested optimization
3. **Strategic manipulation:** VCG mechanisms vulnerable to false-name bids (NP-hard to manipulate optimally)
4. **Information asymmetry:** Cross-border M&A due diligence with adverse selection and moral hazard
5. **Multi-jurisdictional complexity:** Cross-border deals require approvals from ≥2 national authorities + supranational bodies (CFIUS, EC)

### 7.2 Data Bottlenecks

1. **Entity resolution at scale:** Oracle batch size limits for large datasets
2. **Valuation uncertainty:** Foreign exchange risk, differing accounting standards (GAAP)
3. **Cultural distance:** "Liability of foreignness" and "double-layered acculturation"
4. **Tacit knowledge:** Embedded assets difficult to identify and value

### 7.3 Algorithmic Bottlenecks

1. **Inapproximability:** Some variants (network defense damage minimization) have no PTAS
2. **Integrality gaps:** LP relaxations may be loose (gap = 2 for network defense)
3. **Local minima:** MINLPs with transaction costs and non-convex constraints
4. **Scalability:** Commercial MIP solvers struggle beyond a few hundred assets

### 7.4 Platform Integration Bottlenecks

1. **Cross-domain complexity:** Different NP-hard problems at each acquisition stage
2. **Real-time requirements:** Auction winner determination must be fast
3. **Explainability:** Defense acquisition requires auditable decisions
4. **Adversarial robustness:** Search ranking and auction mechanisms face strategic manipulation

---

## 8. Cross-Cutting Themes

### 8.1 The P vs NP Divide in Practice

- **Heuristica world:** NP problems are hard in worst case but easy on average (Impagliazzo 1995)
- **Small instances:** "NP-hard but n is tiny" is the most under-exploited situation in industry
- **Structured instances:** Real-world acquisition problems often have exploitable structure

### 8.2 Approximation as a First-Class Citizen

- **SLA-bound guarantees:** Christofides 1.5-approx, greedy ln(d)-approx for set cover
- **FPTAS for weakly NP-hard:** Knapsack admits fully polynomial-time approximation schemes
- **Resource augmentation:** 2-approximation for network defense with 2R resource

### 8.3 ML as a Heuristic Generator

- **Automated discovery:** Systematic search over program spaces for heuristics
- **Machine-checkable certificates:** Auditable even for opaque ML-generated solutions
- **LLM reasoning:** NP-hard problems as training corpus for deep reasoning

### 8.4 Game-Theoretic Security

- **Stackelberg games:** Defender commits first, attacker best-responds
- **Hard-to-manipulate mechanisms:** Relaxing strategyproofness to NP-hard manipulation
- **Repeated interactions:** Infinitely Repeated Prisoner's Dilemma for ranking manipulation

---

## 9. Citations

1. Brown, G., et al. "Applying Defender-Attacker (-Defender) Optimization..." Naval Postgraduate School.
2. Li, X., et al. "Defending with Shared Resources on a Network." AAAI 2007.
3. Jain, M., et al. "Mixed Strategies for Security Games with General Defending Requirements." IJCAI 2022.
4. Bienstock, D. "Computational study of a family of mixed-integer quadratic programming problems." Mathematical Programming, 1996.
5. Bertsimas, D., et al. "Best subset selection via modern optimization." 2016.
6. Sherrington, D. & Kirkpatrick, S. "Solvable model of a spin-glass." Physical Review Letters, 1975.
7. Lucas, A. "Ising formulations of many NP problems." Frontiers in Physics, 2014.
8. Moehle, N., et al. "Taxable portfolio optimization with transaction costs." 2021.
9. Shimizu, K., et al. "Cross-border M&A research." 2004.
10. Erel, I., et al. "Contracting Costs and Information Asymmetry Reduction in Cross-Border M&A." Journal of Management Studies, 2010.
11. Sandholm, T. "Winner Determination in Combinatorial Auctions." CMU.
12. Rothkopf, M., et al. "Computationally manageable combinatorial auctions." 1998.
13. Lehmann, D., et al. "Winner determination in combinatorial auctions." 2003.
14. Parkes, D. "Hard-to-Manipulate VCG-Based Auctions." Harvard.
15. Yokoo, M., et al. "False-name-proof mechanisms." 2002.
16. Nisan, N. & Ronen, A. "Computationally feasible VCG mechanisms." 2000.
17. Ekim, T., et al. "Defensive domination problems." 2008.
18. Li, J., et al. "Graph-R1: Unleashing LLM Reasoning with NP-Hard Graph Problems." Arxiv 2025.
19. Impagliazzo, R. "A personal view of average-case complexity." 1995.
20. Garey, M. & Johnson, D. "Computers and Intractability." 1979.
21. Karp, R. "Reducibility among combinatorial problems." 1972.
22. Cook, S. "The complexity of theorem proving procedures." 1971.
23. Christofides, N. "Worst-case analysis of a new heuristic for the travelling salesman problem." 1976.
24. Ibarra, O. & Kim, C. "Fast approximation algorithms for the knapsack and sum of subset problems." JACM, 1975.
25. Johnson, D. "Approximation algorithms for combinatorial problems." 1974.
26. Mugel, S., et al. "Variational neural annealing for portfolio optimization." 2022.
27. Gan, J., et al. "Patching algorithms for security games." 2017.
28. Korzhyk, D., et al. "Stackelberg vs. Nash in security games." 2010.
29. Bazgan, C. & Paschos, T. "Approximation of MAX-DNF." 2003.
30. van Hoesel, S. & Müller, R. "Optimization in combinatorial auctions." 2001.
31. Keil, J. "Job interval selection problem." 1992.
32. Spieksma, F. "Approximability of interval scheduling." 1999.

---

## 10. Implications for Acquisition Platform Design

### 10.1 Architecture Recommendations

1. **Hybrid solver stack:** Combine exact MIP solvers (small instances) with metaheuristics (large instances)
2. **Approximation-first design:** Build SLAs around provable approximation ratios
3. **ML-augmented optimization:** Use RL/LLM for heuristic generation and warm-starting
4. **Decomposition:** Exploit problem structure (treewidth, single-index, separability)
5. **Game-theoretic layer:** Model adversarial interactions explicitly

### 10.2 Technology Transfer Specific

- **Knapsack-based screening:** Use FPTAS for technology portfolio selection
- **Entity resolution:** Deploy batched oracle queries with pERbacco-style algorithms
- **Cross-border complexity:** Model multi-jurisdictional approval as constraint satisfaction

### 10.3 Defense Acquisition Specific

- **Security games:** Use Patching algorithm for mixed strategy computation
- **Network defense:** LP-rounding with 2-approximation guarantee
- **Auction mechanisms:** Design for hard-to-manipulate (not fully strategyproof) mechanisms

---

*End of Wave 3 Research Document*
