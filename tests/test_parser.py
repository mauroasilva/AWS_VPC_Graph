import unittest

from vpc_graph.parser import parse_lines

V2_LINE = (
    "2 123456789010 eni-1235b8ca123456789 172.31.16.139 172.31.16.21 "
    "20641 22 6 20 4249 1418530010 1418530070 ACCEPT OK"
)


class ParseLinesTest(unittest.TestCase):
    def test_parses_default_v2_record(self):
        records = list(parse_lines([V2_LINE]))
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.src_ip, "172.31.16.139")
        self.assertEqual(record.dst_ip, "172.31.16.21")
        self.assertEqual(record.src_port, 20641)
        self.assertEqual(record.dst_port, 22)
        self.assertEqual(record.protocol, "6")
        self.assertEqual(record.start, 1418530010)
        self.assertEqual(record.end, 1418530070)
        self.assertEqual(record.action, "ACCEPT")

    def test_skips_blank_lines_and_comments(self):
        records = list(parse_lines(["", "   ", "# comment", V2_LINE]))
        self.assertEqual(len(records), 1)

    def test_skips_nodata_and_skipdata(self):
        nodata = (
            "2 123456789010 eni-1235b8ca123456789 - - - - - - - "
            "1418530010 1418530070 - NODATA"
        )
        skipdata = nodata.replace("NODATA", "SKIPDATA")
        records = list(parse_lines([nodata, skipdata, V2_LINE]))
        self.assertEqual(len(records), 1)

    def test_skips_records_with_missing_required_fields(self):
        broken = (
            "2 123456789010 eni-1235b8ca123456789 - 172.31.16.21 "
            "20641 22 6 20 4249 1418530010 1418530070 ACCEPT OK"
        )
        self.assertEqual(list(parse_lines([broken])), [])

    def test_skips_malformed_records(self):
        self.assertEqual(list(parse_lines(["2 123 eni-1 not enough"])), [])

    def test_header_line_switches_field_order(self):
        lines = [
            "srcaddr dstaddr srcport dstport start end action log-status",
            "10.0.0.1 10.0.0.2 4711 80 100 200 ACCEPT OK",
        ]
        records = list(parse_lines(lines))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].src_ip, "10.0.0.1")
        self.assertEqual(records[0].dst_port, 80)

    def test_explicit_fields_argument(self):
        records = list(
            parse_lines(
                ["10.0.0.1 10.0.0.2 4711 80 100 200"],
                fields=["srcaddr", "dstaddr", "srcport", "dstport", "start", "end"],
            )
        )
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].action, "-")


if __name__ == "__main__":
    unittest.main()
