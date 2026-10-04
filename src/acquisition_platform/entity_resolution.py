"""Entity resolution module.

Entity resolution (also known as record linkage or deduplication) is the
task of finding records that refer to the same real-world entity. The
general problem of pairwise entity resolution is NP-hard: given *n*
entities there are O(n^2) possible pairs to compare, and finding the
optimal clustering is at least as hard as correlation clustering.

This module implements a blocking + union-find approach that avoids the
full O(n^2) comparison in practice:

1. Normalize names (lowercase, strip punctuation).
2. Block by the first 3 characters of the normalized name, reducing the
   candidate pairs from O(n^2) to O(sum of block_size^2).
3. Within each block, compare pairs using Jaro-Winkler similarity on the
   normalized name plus a domain-match bonus.
4. If the combined similarity meets the threshold, union the pair.
5. The canonical name of a cluster is the most frequent original name
   (first encountered wins ties).
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass


@dataclass
class ResolvedEntity:
    """A resolved entity with its cluster members and canonical name."""

    entities: list[dict]
    canonical_name: str


@dataclass
class EntityCluster:
    """A cluster of entities that refer to the same real-world entity."""

    entities: list[dict]
    canonical_name: str


def _normalize(name: str) -> str:
    """Normalize a name: lowercase and strip punctuation."""
    return re.sub(r"[^\w\s]", "", name.lower()).strip()


def _jaro_winkler(s1: str, s2: str) -> float:
    """Compute Jaro-Winkler similarity between two strings.

    Returns a value in [0, 1]. Identical strings return 1.0.
    """
    if s1 == s2:
        return 1.0

    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    # --- Jaro similarity ---
    match_window = max(len1, len2) // 2 - 1
    if match_window < 0:
        match_window = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0

    for i in range(len1):
        start = max(0, i - match_window)
        end = min(len2, i + match_window + 1)
        for j in range(start, end):
            if s2_matches[j]:
                continue
            if s1[i] == s2[j]:
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break

    if matches == 0:
        return 0.0

    # Count transpositions
    transpositions = 0
    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1
    transpositions //= 2

    jaro = (
        matches / len1
        + matches / len2
        + (matches - transpositions) / matches
    ) / 3.0

    # --- Jaro-Winkler adjustment ---
    prefix_len = 0
    for i in range(min(4, len1, len2)):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break

    jw = jaro + prefix_len * 0.1 * (1.0 - jaro)
    return min(jw, 1.0)


class _UnionFind:
    """Union-Find (disjoint set) data structure with path compression."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        """Find the root of x with path compression."""
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x: int, y: int) -> None:
        """Union the sets containing x and y."""
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1


class EntityResolver:
    """Resolve entities into clusters using blocking + Jaro-Winkler + union-find.

    Parameters
    ----------
    threshold : float
        Minimum similarity score (Jaro-Winkler + domain bonus) for two
        entities to be clustered together.  Defaults to 0.85.
    """

    def __init__(self, threshold: float = 0.85) -> None:
        self.threshold = threshold
        self.comparison_count: int = 0

    def resolve(self, entities: list[dict]) -> list[EntityCluster]:
        """Resolve a list of entity dicts into clusters.

        Each entity dict should have at least a ``name`` key and
        optionally a ``domain`` key.

        Returns
        -------
        list[EntityCluster]
            A list of clusters, each containing the grouped entities and
            their canonical name.
        """
        self.comparison_count = 0

        if not entities:
            return []

        n = len(entities)
        uf = _UnionFind(n)

        # Normalize names and block by first 3 characters
        normalized = [_normalize(e.get("name", "")) for e in entities]
        blocks: dict[str, list[int]] = defaultdict(list)
        for i, norm in enumerate(normalized):
            blocks[norm[:3]].append(i)

        # Compare pairs within each block
        for indices in blocks.values():
            for a in range(len(indices)):
                for b in range(a + 1, len(indices)):
                    i, j = indices[a], indices[b]
                    self.comparison_count += 1

                    sim = _jaro_winkler(normalized[i], normalized[j])

                    # Domain match bonus
                    dom_i = entities[i].get("domain", "")
                    dom_j = entities[j].get("domain", "")
                    if dom_i and dom_j and dom_i == dom_j:
                        sim = min(sim + 0.2, 1.0)

                    if sim >= self.threshold:
                        uf.union(i, j)

        # Group indices by their union-find root
        groups: dict[int, list[int]] = defaultdict(list)
        for i in range(n):
            groups[uf.find(i)].append(i)

        # Build EntityCluster objects
        result: list[EntityCluster] = []
        for indices in groups.values():
            cluster_entities = [entities[i] for i in indices]
            canonical = self._canonical_name(cluster_entities)
            result.append(
                EntityCluster(entities=cluster_entities, canonical_name=canonical)
            )

        return result

    @staticmethod
    def _canonical_name(entities: list[dict]) -> str:
        """Pick the most frequent name; first encountered wins ties."""
        names = [e.get("name", "") for e in entities]
        counts = Counter(names)
        max_count = max(counts.values())
        for name in names:
            if counts[name] == max_count:
                return name
        return names[0]  # unreachable when entities is non-empty
