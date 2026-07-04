import unittest

from vpc_graph.aggregator import aggregate, format_timestamp
from vpc_graph.parser import FlowRecord


def make_record(**overrides):
    defaults = dict(
        src_ip="172.31.16.139",
        dst_ip="10.0.0.5",
        src_port=21251,
        dst_port=22,
        protocol="6",
        start=1418530010,
        end=1418530070,
        action="ACCEPT",
    )
    defaults.update(overrides)
    return FlowRecord(**defaults)


class AggregateTest(unittest.TestCase):
    def test_source_port_range_label_matches_requirement_example(self):
        # Three connections with src ports 21251, 22022, 22353 -> "21251 - 22353"
        records = [
            make_record(src_port=21251),
            make_record(src_port=22022),
            make_record(src_port=22353),
        ]
        edges = aggregate(records)
        self.assertEqual(len(edges), 1)
        edge = edges[("172.31.16.139", "10.0.0.5", 22)]
        self.assertEqual(edge.src_port_range, "21251 - 22353")
        self.assertEqual(edge.connection_count, 3)

    def test_single_source_port_shows_single_value(self):
        edges = aggregate([make_record(src_port=21251)])
        edge = next(iter(edges.values()))
        self.assertEqual(edge.src_port_range, "21251")

    def test_one_edge_per_destination_port(self):
        records = [make_record(dst_port=22), make_record(dst_port=443)]
        edges = aggregate(records)
        self.assertEqual(
            set(edges),
            {("172.31.16.139", "10.0.0.5", 22), ("172.31.16.139", "10.0.0.5", 443)},
        )

    def test_first_and_last_seen(self):
        records = [
            make_record(start=200, end=250),
            make_record(start=100, end=150),
            make_record(start=300, end=400),
        ]
        edge = next(iter(aggregate(records).values()))
        self.assertEqual(edge.first_seen, 100)
        self.assertEqual(edge.last_seen, 400)

    def test_label_contains_all_required_parts(self):
        records = [
            make_record(src_port=21251, start=100, end=150),
            make_record(src_port=22353, start=200, end=250),
        ]
        edge = next(iter(aggregate(records).values()))
        self.assertIn("21251 - 22353", edge.label)
        self.assertIn("dst port: 22", edge.label)
        self.assertIn(format_timestamp(100), edge.label)
        self.assertIn(format_timestamp(250), edge.label)

    def test_action_filter(self):
        records = [make_record(action="ACCEPT"), make_record(action="REJECT")]
        edges = aggregate(records, action="ACCEPT")
        self.assertEqual(next(iter(edges.values())).connection_count, 1)

    def test_direction_matters(self):
        records = [
            make_record(src_ip="a", dst_ip="b"),
            make_record(src_ip="b", dst_ip="a"),
        ]
        self.assertEqual(len(aggregate(records)), 2)


class FormatTimestampTest(unittest.TestCase):
    def test_formats_as_utc(self):
        self.assertEqual(format_timestamp(1418530010), "2014-12-14 04:06:50Z")


if __name__ == "__main__":
    unittest.main()
