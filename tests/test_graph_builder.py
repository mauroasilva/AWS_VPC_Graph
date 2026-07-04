import unittest

from vpc_graph.aggregator import ConnectionEdge
from vpc_graph.graph_builder import build_graph, compute_rank_widths


def make_edge(src, dst, dst_port, count, src_ports=(1000, 2000), seen=(100, 200)):
    edge = ConnectionEdge(src_ip=src, dst_ip=dst, dst_port=dst_port)
    edge.connection_count = count
    edge.min_src_port, edge.max_src_port = min(src_ports), max(src_ports)
    edge.first_seen, edge.last_seen = seen
    edge.protocols = {"6"}
    edge.actions = {"ACCEPT"}
    return edge


class ComputeRankWidthsTest(unittest.TestCase):
    def test_widths_follow_rank_not_magnitude(self):
        # Counts 100, 3, 2: widths must be evenly spaced by rank, i.e. the
        # jump from 100 to 3 must equal the jump from 3 to 2.
        widths = compute_rank_widths([100, 3, 2], min_width=1.0, max_width=10.0)
        self.assertEqual(widths[100], 10.0)
        self.assertEqual(widths[2], 1.0)
        self.assertAlmostEqual(widths[100] - widths[3], widths[3] - widths[2])

    def test_highest_count_gets_largest_width(self):
        widths = compute_rank_widths([5, 50, 500])
        self.assertGreater(widths[500], widths[50])
        self.assertGreater(widths[50], widths[5])

    def test_ties_share_a_width(self):
        widths = compute_rank_widths([7, 7, 3], min_width=1.0, max_width=10.0)
        self.assertEqual(widths, {7: 10.0, 3: 1.0})

    def test_single_count_gets_max_width(self):
        self.assertEqual(compute_rank_widths([4], max_width=8.0), {4: 8.0})

    def test_empty_input(self):
        self.assertEqual(compute_rank_widths([]), {})


class BuildGraphTest(unittest.TestCase):
    def test_nodes_are_ips_and_edges_keyed_by_dst_port(self):
        edges = [
            make_edge("10.0.0.1", "10.0.0.2", 22, count=3),
            make_edge("10.0.0.1", "10.0.0.2", 443, count=5),
        ]
        graph = build_graph(edges)
        self.assertEqual(set(graph.nodes), {"10.0.0.1", "10.0.0.2"})
        self.assertEqual(graph.number_of_edges(), 2)
        self.assertTrue(graph.has_edge("10.0.0.1", "10.0.0.2", key=22))
        self.assertTrue(graph.has_edge("10.0.0.1", "10.0.0.2", key=443))

    def test_edge_widths_are_ranked(self):
        edges = [
            make_edge("a", "b", 22, count=3),
            make_edge("a", "c", 53, count=10),
            make_edge("b", "c", 80, count=1),
        ]
        graph = build_graph(edges, min_width=1.0, max_width=10.0)
        w_by_port = {
            key: data["width"] for _, _, key, data in graph.edges(keys=True, data=True)
        }
        self.assertEqual(w_by_port[53], 10.0)  # highest count -> widest
        self.assertEqual(w_by_port[80], 1.0)  # lowest count -> narrowest
        self.assertTrue(w_by_port[80] < w_by_port[22] < w_by_port[53])
        ranks = {
            key: data["rank"] for _, _, key, data in graph.edges(keys=True, data=True)
        }
        self.assertEqual(ranks, {53: 1, 22: 2, 80: 3})

    def test_edge_attributes(self):
        graph = build_graph(
            [make_edge("a", "b", 22, count=2, src_ports=(21251, 22353))]
        )
        data = graph.get_edge_data("a", "b", key=22)
        self.assertEqual(data["src_port_range"], "21251 - 22353")
        self.assertEqual(data["connection_count"], 2)
        self.assertIn("21251 - 22353", data["label"])


if __name__ == "__main__":
    unittest.main()
