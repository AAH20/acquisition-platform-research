"""Graph analysis module.

Provides graph construction, centrality analysis, community detection,
path analysis, density calculation, influence scoring, resilience
assessment, and visualization data generation.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from acquisition_platform.exceptions import NodeNotFoundError, ValidationError


@dataclass
class GraphNode:
    """A node in the graph."""

    node_id: str
    label: str
    weight: float
    category: str


@dataclass
class GraphEdge:
    """An edge in the graph."""

    source: str
    target: str
    weight: float
    edge_type: str


@dataclass
class GraphResult:
    """Result of a full graph analysis report."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    density: float
    communities: list[list[str]]


class GraphAnalyzer:
    """Graph analyzer supporting construction, metrics, and reporting."""

    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge] = []
        self._adj: dict[str, list[str]] = {}

    @property
    def nodes(self) -> list[GraphNode]:
        """Return all nodes in insertion order."""
        return list(self._nodes.values())

    @property
    def edges(self) -> list[GraphEdge]:
        """Return all edges."""
        return list(self._edges)

    def add_node(
        self, node_id: str, label: str, weight: float, category: str
    ) -> GraphNode:
        """Add a node to the graph.

        Args:
            node_id: Unique identifier for the node.
            label: Human-readable label.
            weight: Node weight (must be non-negative).
            category: Category classification.

        Returns:
            The created GraphNode.

        Raises:
            ValidationError: If node_id already exists or weight is negative.
        """
        if node_id in self._nodes:
            raise ValidationError(f"Node '{node_id}' already exists")
        if weight < 0:
            raise ValidationError("Node weight must be non-negative")
        node = GraphNode(node_id=node_id, label=label, weight=weight, category=category)
        self._nodes[node_id] = node
        self._adj[node_id] = []
        return node

    def add_edge(
        self, source: str, target: str, weight: float, edge_type: str
    ) -> GraphEdge:
        """Add an undirected edge between two nodes.

        Args:
            source: Source node ID.
            target: Target node ID.
            weight: Edge weight (must be non-negative).
            edge_type: Type classification for the edge.

        Returns:
            The created GraphEdge.

        Raises:
            NodeNotFoundError: If source or target node does not exist.
            ValidationError: If weight is negative.
        """
        if source not in self._nodes:
            raise NodeNotFoundError(f"Source node '{source}' not found")
        if target not in self._nodes:
            raise NodeNotFoundError(f"Target node '{target}' not found")
        if weight < 0:
            raise ValidationError("Edge weight must be non-negative")
        edge = GraphEdge(source=source, target=target, weight=weight, edge_type=edge_type)
        self._edges.append(edge)
        self._adj[source].append(target)
        self._adj[target].append(source)
        return edge

    def centrality(self, node_id: str) -> float:
        """Calculate degree centrality for a node.

        Degree centrality is the fraction of nodes this node is connected to.

        Args:
            node_id: The node to calculate centrality for.

        Returns:
            Degree centrality score in [0, 1].

        Raises:
            NodeNotFoundError: If the node does not exist.
        """
        if node_id not in self._nodes:
            raise NodeNotFoundError(f"Node '{node_id}' not found")
        n = len(self._nodes)
        if n <= 1:
            return 0.0
        return len(self._adj[node_id]) / (n - 1)

    def detect_communities(self) -> list[list[str]]:
        """Detect communities via greedy modularity optimization.

        Uses a Louvain-style local-moving phase: each node starts in its
        own community and is repeatedly moved to the neighboring community
        that yields the largest modularity gain, until no move improves
        modularity.

        Returns:
            List of communities, each a sorted list of node IDs.
        """
        if not self._nodes:
            return []
        node_ids = list(self._nodes.keys())
        if len(node_ids) == 1:
            return [node_ids]

        # Build weighted adjacency (undirected, weights summed per pair)
        adj: dict[str, dict[str, float]] = {nid: {} for nid in node_ids}
        for e in self._edges:
            adj[e.source][e.target] = adj[e.source].get(e.target, 0.0) + e.weight
            adj[e.target][e.source] = adj[e.target].get(e.source, 0.0) + e.weight

        degree = {nid: sum(adj[nid].values()) for nid in node_ids}
        m2 = sum(degree.values())  # twice the total edge weight
        if m2 == 0.0:
            return [[nid] for nid in node_ids]

        # Start: each node in its own community
        comm = {nid: i for i, nid in enumerate(node_ids)}
        comm_members: dict[int, set[str]] = {i: {nid} for i, nid in enumerate(node_ids)}

        def modularity() -> float:
            q = 0.0
            for members in comm_members.values():
                internal = sum(adj[u].get(v, 0.0) for u in members for v in members)
                total = sum(degree[u] for u in members)
                q += internal / m2 - (total / m2) ** 2
            return q

        improved = True
        while improved:
            improved = False
            for nid in node_ids:
                current_q = modularity()
                best_comm = comm[nid]
                best_gain = 0.0
                candidate_comms = {comm[nb] for nb in adj[nid]}
                for c in candidate_comms:
                    if c == comm[nid]:
                        continue
                    old_c = comm[nid]
                    # Tentatively move nid from old_c to c
                    comm_members[old_c].discard(nid)
                    if not comm_members[old_c]:
                        del comm_members[old_c]
                    comm[nid] = c
                    comm_members.setdefault(c, set()).add(nid)
                    gain = modularity() - current_q
                    if gain > best_gain + 1e-12:
                        best_gain = gain
                        best_comm = c
                    # Revert the tentative move
                    comm_members[c].discard(nid)
                    if not comm_members[c]:
                        del comm_members[c]
                    comm[nid] = old_c
                    comm_members.setdefault(old_c, set()).add(nid)
                if best_comm != comm[nid]:
                    old_c = comm[nid]
                    comm_members[old_c].discard(nid)
                    if not comm_members[old_c]:
                        del comm_members[old_c]
                    comm[nid] = best_comm
                    comm_members.setdefault(best_comm, set()).add(nid)
                    improved = True

        return [sorted(members) for members in comm_members.values()]

    def shortest_path(self, source: str, target: str) -> list[str]:
        """Find the shortest path between two nodes using BFS.

        Args:
            source: Starting node ID.
            target: Target node ID.

        Returns:
            List of node IDs forming the shortest path, or empty list
            if no path exists.
        """
        if source not in self._nodes or target not in self._nodes:
            return []
        if source == target:
            return [source]

        visited: set[str] = {source}
        queue: deque[tuple[str, list[str]]] = deque([(source, [source])])

        while queue:
            current, path = queue.popleft()
            for neighbor in self._adj[current]:
                if neighbor == target:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return []

    def network_density(self) -> float:
        """Calculate network density.

        Density is the ratio of actual edges to possible edges in an
        undirected graph: 2*E / (N*(N-1)).

        Returns:
            Density value in [0, 1].
        """
        n = len(self._nodes)
        if n <= 1:
            return 0.0
        return (2 * len(self._edges)) / (n * (n - 1))

    def influence_score(self, node_id: str) -> float:
        """Calculate influence score for a node.

        Influence combines degree centrality with node weight:
        score = centrality * (1 + weight)

        Args:
            node_id: The node to score.

        Returns:
            Influence score (higher = more influential).

        Raises:
            NodeNotFoundError: If the node does not exist.
        """
        if not self._nodes:
            return 0.0
        if node_id not in self._nodes:
            raise NodeNotFoundError(f"Node '{node_id}' not found")
        node = self._nodes[node_id]
        return self.centrality(node_id) * (1.0 + node.weight)

    def network_resilience(self) -> float:
        """Calculate network resilience.

        Resilience is measured as the fraction of node pairs that
        remain connected (have a path between them). A fully connected
        graph has resilience 1.0; a disconnected graph has lower resilience.

        Returns:
            Resilience score in [0, 1].
        """
        n = len(self._nodes)
        if n <= 1:
            return 0.0

        node_ids = list(self._nodes.keys())
        connected_pairs = 0
        total_pairs = 0

        for i in range(n):
            for j in range(i + 1, n):
                total_pairs += 1
                if self._has_path(node_ids[i], node_ids[j]):
                    connected_pairs += 1

        return connected_pairs / total_pairs if total_pairs > 0 else 0.0

    def _has_path(self, source: str, target: str) -> bool:
        """Check if a path exists between two nodes using BFS."""
        if source == target:
            return True
        visited: set[str] = {source}
        queue: deque[str] = deque([source])
        while queue:
            current = queue.popleft()
            for neighbor in self._adj[current]:
                if neighbor == target:
                    return True
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

    def generate_graph_report(self) -> GraphResult:
        """Generate a full graph analysis report.

        Returns:
            GraphResult with nodes, edges, density, and communities.
        """
        return GraphResult(
            nodes=self.nodes,
            edges=self.edges,
            density=self.network_density(),
            communities=self.detect_communities(),
        )

    def generate_viz_data(self) -> dict[str, Any]:
        """Generate visualization-compatible data.

        Returns:
            Dict with 'nodes' and 'edges' lists suitable for
            rendering in visualization libraries (e.g., D3, vis.js).
        """
        return {
            "nodes": [
                {
                    "id": n.node_id,
                    "label": n.label,
                    "weight": n.weight,
                    "category": n.category,
                }
                for n in self._nodes.values()
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "weight": e.weight,
                    "edge_type": e.edge_type,
                }
                for e in self._edges
            ],
        }
