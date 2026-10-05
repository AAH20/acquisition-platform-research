"""Tests for graph analysis module."""
import pytest

from acquisition_platform.exceptions import EmptyInputError, NodeNotFoundError
from acquisition_platform.graph_analysis import (
    GraphAnalyzer,
    GraphEdge,
    GraphNode,
    GraphResult,
)


class TestGraphAnalysis:
    """TDD tests for the graph analysis module."""

    def _build_sample_graph(self) -> GraphAnalyzer:
        """Build a small sample graph for testing."""
        g = GraphAnalyzer()
        g.add_node("a", "Alice", 1.0, "person")
        g.add_node("b", "Bob", 1.0, "person")
        g.add_node("c", "Carol", 1.0, "person")
        g.add_node("d", "Dave", 1.0, "person")
        g.add_edge("a", "b", 1.0, "knows")
        g.add_edge("b", "c", 1.0, "knows")
        g.add_edge("c", "d", 1.0, "knows")
        g.add_edge("a", "d", 1.0, "knows")
        return g

    def test_network_construction(self):
        """Network is constructed with nodes and edges."""
        g = self._build_sample_graph()
        assert len(g.nodes) == 4
        assert len(g.edges) == 4
        assert g.nodes[0].node_id == "a"
        assert g.nodes[0].label == "Alice"
        assert g.nodes[0].weight == 1.0
        assert g.nodes[0].category == "person"
        assert g.edges[0].source == "a"
        assert g.edges[0].target == "b"
        assert g.edges[0].weight == 1.0
        assert g.edges[0].edge_type == "knows"

    def test_centrality(self):
        """Centrality is calculated for a node."""
        g = self._build_sample_graph()
        score = g.centrality("a")
        assert isinstance(score, float)
        assert score > 0.0
        # Node 'a' has degree 2, node 'b' has degree 2, node 'c' has degree 2, node 'd' has degree 2
        # All nodes have the same degree in this graph, so centrality should be equal
        assert g.centrality("a") == g.centrality("b")

    def test_empty_graph(self):
        """Empty graph returns defaults."""
        g = GraphAnalyzer()
        assert g.nodes == []
        assert g.edges == []
        assert g.network_density() == 0.0
        assert g.detect_communities() == []
        assert g.network_resilience() == 0.0
        assert g.shortest_path("a", "b") == []
        assert g.influence_score("a") == 0.0
        report = g.generate_graph_report()
        assert report.nodes == []
        assert report.edges == []
        assert report.density == 0.0
        assert report.communities == []

    def test_community_detection(self):
        """Communities are detected in the graph."""
        g = GraphAnalyzer()
        # Two cliques connected by a bridge
        g.add_node("a", "A", 1.0, "person")
        g.add_node("b", "B", 1.0, "person")
        g.add_node("c", "C", 1.0, "person")
        g.add_node("d", "D", 1.0, "person")
        g.add_node("e", "E", 1.0, "person")
        g.add_node("f", "F", 1.0, "person")
        g.add_edge("a", "b", 1.0, "knows")
        g.add_edge("b", "c", 1.0, "knows")
        g.add_edge("a", "c", 1.0, "knows")
        g.add_edge("d", "e", 1.0, "knows")
        g.add_edge("e", "f", 1.0, "knows")
        g.add_edge("d", "f", 1.0, "knows")
        g.add_edge("c", "d", 1.0, "bridge")
        communities = g.detect_communities()
        assert len(communities) == 2
        # Each community should have 3 members
        sizes = sorted(len(c) for c in communities)
        assert sizes == [3, 3]

    def test_path_analysis(self):
        """Shortest path is found between nodes."""
        g = self._build_sample_graph()
        path = g.shortest_path("a", "c")
        assert path == ["a", "b", "c"]
        # Direct edge a-d exists, so path a->d is length 1
        path_ad = g.shortest_path("a", "d")
        assert path_ad == ["a", "d"]

    def test_network_density(self):
        """Network density is calculated."""
        g = self._build_sample_graph()
        density = g.network_density()
        assert isinstance(density, float)
        assert 0.0 < density <= 1.0
        # 4 nodes, 4 edges, undirected: density = 2*4 / (4*3) = 8/12 = 0.667
        assert density == pytest.approx(2 * 4 / (4 * 3))

    def test_graph_report(self):
        """Graph report is generated with all fields."""
        g = self._build_sample_graph()
        report = g.generate_graph_report()
        assert isinstance(report, GraphResult)
        assert len(report.nodes) == 4
        assert len(report.edges) == 4
        assert report.density == pytest.approx(2 * 4 / (4 * 3))
        assert isinstance(report.communities, list)

    def test_influence_scoring(self):
        """Influence score is calculated for a node."""
        g = GraphAnalyzer()
        g.add_node("hub", "Hub", 1.0, "person")
        g.add_node("leaf1", "L1", 1.0, "person")
        g.add_node("leaf2", "L2", 1.0, "person")
        g.add_node("leaf3", "L3", 1.0, "person")
        g.add_edge("hub", "leaf1", 1.0, "knows")
        g.add_edge("hub", "leaf2", 1.0, "knows")
        g.add_edge("hub", "leaf3", 1.0, "knows")
        hub_score = g.influence_score("hub")
        leaf_score = g.influence_score("leaf1")
        assert hub_score > leaf_score
        assert hub_score > 0.0

    def test_network_resilience(self):
        """Network resilience is scored."""
        g = self._build_sample_graph()
        resilience = g.network_resilience()
        assert isinstance(resilience, float)
        assert 0.0 <= resilience <= 1.0

    def test_visualization_data(self):
        """Visualization data is generated."""
        g = self._build_sample_graph()
        viz = g.generate_viz_data()
        assert "nodes" in viz
        assert "edges" in viz
        assert len(viz["nodes"]) == 4
        assert len(viz["edges"]) == 4
        assert viz["nodes"][0]["id"] == "a"
        assert viz["nodes"][0]["label"] == "Alice"
        assert viz["edges"][0]["source"] == "a"
        assert viz["edges"][0]["target"] == "b"

    def test_add_node_returns_node(self):
        """add_node returns a GraphNode."""
        g = GraphAnalyzer()
        node = g.add_node("x", "X", 2.0, "test")
        assert isinstance(node, GraphNode)
        assert node.node_id == "x"
        assert node.label == "X"
        assert node.weight == 2.0
        assert node.category == "test"

    def test_add_edge_returns_edge(self):
        """add_edge returns a GraphEdge."""
        g = GraphAnalyzer()
        g.add_node("a", "A", 1.0, "person")
        g.add_node("b", "B", 1.0, "person")
        edge = g.add_edge("a", "b", 1.0, "knows")
        assert isinstance(edge, GraphEdge)
        assert edge.source == "a"
        assert edge.target == "b"
        assert edge.weight == 1.0
        assert edge.edge_type == "knows"

    def test_centrality_unknown_node_raises(self):
        """Centrality for unknown node raises NodeNotFoundError."""
        g = GraphAnalyzer()
        with pytest.raises(NodeNotFoundError):
            g.centrality("nonexistent")

    def test_shortest_path_no_path_returns_empty(self):
        """Shortest path returns empty list when no path exists."""
        g = GraphAnalyzer()
        g.add_node("a", "A", 1.0, "person")
        g.add_node("b", "B", 1.0, "person")
        assert g.shortest_path("a", "b") == []

    def test_duplicate_node_raises(self):
        """Adding a duplicate node raises ValidationError."""
        g = GraphAnalyzer()
        g.add_node("a", "A", 1.0, "person")
        with pytest.raises(Exception):
            g.add_node("a", "A2", 1.0, "person")

    def test_edge_unknown_node_raises(self):
        """Adding an edge with unknown node raises NodeNotFoundError."""
        g = GraphAnalyzer()
        g.add_node("a", "A", 1.0, "person")
        with pytest.raises(NodeNotFoundError):
            g.add_edge("a", "nonexistent", 1.0, "knows")
