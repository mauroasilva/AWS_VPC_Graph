"""Command-line interface for vpc_graph.

Example:

    python -m vpc_graph sample_data/sample_flow_log.txt -o vpc_graph.html
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional, Sequence

import networkx as nx

from vpc_graph.aggregator import aggregate
from vpc_graph.discovery import expand_inputs
from vpc_graph.graph_builder import (
    DEFAULT_MAX_WIDTH,
    DEFAULT_MIN_WIDTH,
    build_graph,
)
from vpc_graph.parser import parse_file
from vpc_graph.renderer import render_html


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vpc-graph",
        description=(
            "Build an interactive connection graph from AWS VPC Flow Logs. "
            "Nodes are IPs; one edge is created per destination port with a "
            "rank-based width (highest connection count = widest edge)."
        ),
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        metavar="FILE_OR_DIR",
        help=(
            "VPC flow log files, and/or folders laid out as "
            "<vpc-id>/<year>/<month>/<day>/*.log (each day folder may hold "
            "many minute-chunk .log files; all are processed)"
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default="vpc_graph.html",
        help="output HTML file (default: %(default)s)",
    )
    parser.add_argument(
        "--graphml",
        metavar="FILE",
        help="also export the graph as GraphML for programmatic use",
    )
    parser.add_argument(
        "--fields",
        metavar="FIELD",
        nargs="+",
        help="explicit field order for custom log formats (e.g. srcaddr dstaddr srcport ...)",
    )
    parser.add_argument(
        "--action",
        choices=("ACCEPT", "REJECT"),
        help="only include records with this action (default: include all)",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=1,
        metavar="N",
        help="drop edges with fewer than N connections (default: %(default)s)",
    )
    parser.add_argument(
        "--min-width",
        type=float,
        default=DEFAULT_MIN_WIDTH,
        help="edge width of the lowest-ranked connection count (default: %(default)s)",
    )
    parser.add_argument(
        "--max-width",
        type=float,
        default=DEFAULT_MAX_WIDTH,
        help="edge width of the highest-ranked connection count (default: %(default)s)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose logging")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    logfiles = expand_inputs(args.inputs)
    if not logfiles:
        print("No log files to process.", file=sys.stderr)
        return 1

    def records():
        for path in logfiles:
            yield from parse_file(path, fields=args.fields)

    edges = aggregate(records(), action=args.action)
    kept = [e for e in edges.values() if e.connection_count >= args.min_count]
    if not kept:
        print("No usable flow records found - nothing to graph.", file=sys.stderr)
        return 1

    graph = build_graph(kept, min_width=args.min_width, max_width=args.max_width)
    output = render_html(graph, args.output)
    print(
        f"Wrote {output} ({graph.number_of_nodes()} nodes, "
        f"{graph.number_of_edges()} edges from "
        f"{sum(e.connection_count for e in kept)} connections "
        f"in {len(logfiles)} file(s))"
    )

    if args.graphml:
        nx.write_graphml(graph, args.graphml)
        print(f"Wrote {args.graphml}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
