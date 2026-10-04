# Wave 2 Research: Recommendation System Module Gap Analysis

**Date:** 2026-10-04
**Focus:** Identify the missing `recommendation.py` module — its expected exports, dependencies, and the NP-hard problem it should solve

---

## 1. Gap Confirmation

### 1.1 File Does Not Exist

```
src/acquisition_platform/
├── __init__.py
├── dynamic_pricing.py
├── entity_resolution.py
├── evolution.py
├── fraud_detection.py
├── matching.py
├── portfolio_optimizer.py
├── search_ranking.py
└── valuation.py
```

**No `recommendation.py` file exists.** The module is referenced in the README architecture but has never been implemented.

### 1.2 Grep Results

```
$ grep -r 'recommendation' src/
src/acquisition_platform/dynamic_pricing.py:  """Compute a price recommendation given market conditions."""
```

Only a single docstring match in `dynamic_pricing.py`. No source file, no import, no test file.

### 1.3 No Other Module Imports From It

```
$ grep -rn 'from.*recommendation\|import.*recommendation' --include='*.py' .
(no results)
```

No module in the codebase imports from `recommendation`. The `__init__.py` does not export any recommendation-related symbols.

---

## 2. README References

The README references the recommendation system in three places:

| Location | Context | Reference |
|----------|---------|-----------|
| Line 208 | Architecture diagram (Output layer) | `O1[Recommendations]` |
| Line 241 | Module interactions diagram (Matching Layer) | `REC[Recommendation System]` |
| Lines 264, 267 | Data flow edges | `FRAUD --> REC`, `RANK --> REC` |

The architecture places the Recommendation System in the **Matching Layer**, receiving inputs from:
- **Fraud Detection** (`FRAUD --> REC`) — fraud signals to filter out bad recommendations
- **Search Ranking** (`RANK --> REC`) — ranked listings as candidate inputs

The output flows to the **Output layer** as `O1[Recommendations]`.

---

## 3. Expected Exports

Based on the pattern established by existing modules and the research document, `recommendation.py` should export:

### 3.1 Data Classes

| Class | Fields | Purpose |
|-------|--------|---------|
| `UserProfile` | `id: str, preferences: dict, history: list[str]` | Buyer/investor profile with behavioral signals |
| `ItemProfile` | `id: str, attributes: dict, category: str, embedding: list[float]` | Target company representation |
| `Recommendation` | `item_id: str, score: float, confidence: float, explanation: str` | Single recommendation result with rationale |
| `RecommendationResult` | `recommendations: list[Recommendation], diversity_score: float, coverage_score: float` | Full result set with quality metrics |

### 3.2 Engine Class

| Class | Methods | Purpose |
|-------|---------|---------|
| `RecommendationEngine` | `recommend(user, items, top_k)`, `update_profile(user_id, interaction)`, `compute_diversity(recommendations)` | Hybrid recommendation engine |

### 3.3 Algorithmic Components

The research document identifies these algorithm families that should be represented:

1. **Collaborative Filtering** — matrix factorization on user-item interaction matrix
2. **Content-Based Filtering** — attribute matching (SIC codes, financials, geography)
3. **Hybrid Scoring** — weighted combination with optimization
4. **Diversity Maximization** — submodular maximization for catalog coverage

---

## 4. NP-Hard Problem

### 4.1 Primary Problem: Diversity-Constrained Top-K Recommendation

The recommendation system should solve the **Diversity-Constrained Top-K Recommendation Problem**, which is NP-hard.

**Formal definition:**
Given a set of items \(I\), a user profile \(u\), a similarity metric \(sim(u, i)\), and a diversity metric \(div(S)\) for any subset \(S \subseteq I\), find the subset \(S^* \subseteq I\) with \(|S^*| = K\) that maximizes:

\[
f(S) = \sum_{i \in S} sim(u, i) + \lambda \cdot div(S)
\]

**NP-hardness proof sketch:**
- The diversity term \(div(S)\) is a submodular function (diminishing returns)
- Maximizing a monotone submodular function under a cardinality constraint is NP-hard
- The greedy algorithm achieves a \((1 - 1/e)\) approximation ratio
- This is the same problem structure as `search_ranking.py` but with the added complexity of hybrid scoring

### 4.2 Secondary Problem: Optimal Weight Optimization

The hybrid scoring weights \(w_{cf}, w_{cb}, w_{div}\) should be optimized using metaheuristic approaches identified in the research:

- **Differential Evolution** — 5.98% F1 improvement, 23.1% ranking accuracy gain
- **Particle Swarm Optimization** — competitive with DE
- **Simulated Annealing** — effective but slower convergence

This is a multi-objective optimization problem (accuracy vs. diversity vs. fairness) that is NP-hard in general.

### 4.3 Relationship to Existing Modules

| Module | NP-Hard Problem | Complexity |
|--------|-----------------|------------|
| `matching.py` | Generalized Assignment Problem (GAP) | Strongly NP-hard |
| `search_ranking.py` | Submodular Maximization | NP-hard, (1-1/e) approx |
| `portfolio_optimizer.py` | Knapsack / Portfolio Optimization | NP-hard |
| `dynamic_pricing.py` | Stackelberg Competition | Sigma_2^p-complete |
| **`recommendation.py`** | **Diversity-Constrained Top-K** | **NP-hard, (1-1/e) approx** |

---

## 5. Integration Points

### 5.1 Inputs (from existing modules)

| Source Module | Output | Use in Recommendation |
|---------------|--------|----------------------|
| `matching.py` | `list[Match]` | Historical buyer-seller interactions for CF |
| `search_ranking.py` | `list[RankedListing]` | Candidate items with relevance scores |
| `fraud_detection.py` | `FraudScore` | Filter out fraudulent targets |
| `entity_resolution.py` | `EntityCluster` | Deduplicate target representations |
| `valuation.py` | `ValuationResult` | Price-aware recommendation scoring |

### 5.2 Outputs (to platform)

| Output | Destination | Description |
|--------|-------------|-------------|
| `RecommendationResult` | Output layer (`O1[Recommendations]`) | Ranked target list with explanations |
| `diversity_score` | Analytics layer | Catalog coverage metric |
| `coverage_score` | Analytics layer | Market segment coverage |

---

## 6. Implementation Recommendations

### 6.1 Suggested Module Structure

```python
# recommendation.py

@dataclass
class UserProfile:
    id: str
    preferences: dict
    history: list[str]

@dataclass
class ItemProfile:
    id: str
    attributes: dict
    category: str
    embedding: list[float]

@dataclass
class Recommendation:
    item_id: str
    score: float
    confidence: float
    explanation: str

@dataclass
class RecommendationResult:
    recommendations: list[Recommendation]
    diversity_score: float
    coverage_score: float

class RecommendationEngine:
    def recommend(
        self,
        user: UserProfile,
        items: list[ItemProfile],
        top_k: int = 10,
    ) -> RecommendationResult: ...

    def update_profile(self, user_id: str, interaction: dict) -> None: ...

    def compute_diversity(self, recommendations: list[Recommendation]) -> float: ...
```

### 6.2 Algorithm

1. **Candidate Generation**: Use `search_ranking.py` output as candidate pool
2. **Fraud Filtering**: Remove items with high fraud scores from `fraud_detection.py`
3. **Hybrid Scoring**: Combine CF score + content-based score + diversity bonus
4. **Greedy Selection**: Iteratively select items that maximize the hybrid objective
5. **Explanation Generation**: Produce human-readable rationale for each recommendation

### 6.3 Complexity

- Candidate generation: O(n log n) via search ranking
- Hybrid scoring: O(n * d) where d = embedding dimension
- Greedy selection: O(k * n) where k = top_k
- **Total: O(n log n + n*d + k*n)** — efficient for production scale

---

## 7. Summary

| Aspect | Finding |
|--------|---------|
| **File exists?** | No — `recommendation.py` is missing |
| **Referenced in README?** | Yes — architecture diagram, module interactions, data flow |
| **Imported by other modules?** | No — no imports found |
| **NP-hard problem** | Diversity-Constrained Top-K Recommendation (submodular maximization) |
| **Expected exports** | `UserProfile`, `ItemProfile`, `Recommendation`, `RecommendationResult`, `RecommendationEngine` |
| **Integration** | Receives from matching, search_ranking, fraud_detection; outputs to platform Output layer |
| **Approximation** | Greedy (1-1/e) approximation for submodular maximization |
