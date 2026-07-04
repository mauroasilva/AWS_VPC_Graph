"""vpc_graph - build a connection graph from AWS VPC Flow Logs.

Pipeline: parse flow log records -> aggregate into per-(src, dst, dst_port)
edges -> build a networkx graph with rank-based edge widths -> render an
interactive HTML visualisation.
"""

from vpc_graph.parser import FlowRecord, parse_file, parse_lines
from vpc_graph.aggregator import ConnectionEdge, aggregate
from vpc_graph.discovery import discover_log_files, expand_inputs
from vpc_graph.graph_builder import build_graph, compute_rank_widths

__version__ = "0.2.0"

__all__ = [
    "FlowRecord",
    "parse_file",
    "parse_lines",
    "discover_log_files",
    "expand_inputs",
    "ConnectionEdge",
    "aggregate",
    "build_graph",
    "compute_rank_widths",
    "__version__",
]
