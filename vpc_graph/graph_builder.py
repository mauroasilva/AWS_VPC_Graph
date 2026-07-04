"""Build a networkx graph from aggregated connection edges.

Edge widths encode a *ranking* of connection counts, not a proportion:
the edge with the highest count gets the largest width, the second-highest
count the second-largest width, and so on. Edges with equal counts share
the same rank and therefore the same width (dense ranking).
"""

from __future__ import annotations

from typing import Dict, Iterable, List

import networkx as nx

from vpc_graph.aggregator import ConnectionEdge

DEFAULT_MIN_WIDTH = 1.0
DEFAULT_MAX_WIDTH = 10.0


def compute_rank_widths(
    counts: Iterable[int],
    min_width: float = DEFAULT_MIN_WIDTH,
    max_width: float = DEFAULT_MAX_WIDTH,
) -> Dict[int, float]:
    """Map each distinct connection count to a width based on its rank.

    The highest count maps to ``max_width``, the lowest to ``min_width``,
    and the ranks in between are spaced evenly - regardless of how far
    apart the counts themselves are.
    """
    distinct: List[int] = sorted(set(counts), reverse=True)
    if not distinct:
        return {}
    if len(distinct) == 1:
        return {distinct[0]: max_width}
    step = (max_width - min_width) / (len(distinct) - 1)
    return {count: max_width - i * step for i, count in enumerate(distinct)}


def build_graph(
    edges: Iterable[ConnectionEdge],
    min_width: float = DEFAULT_MIN_WIDTH,
    max_width: float = DEFAULT_MAX_WIDTH,
) -> nx.MultiDiGraph:
    """Build a directed multigraph: IP nodes, one edge per destination port.

    Each edge carries ``width`` (rank-based), ``rank`` (1 = highest count),
    ``label`` and the underlying aggregate values as attributes.
    """
    edge_list = list(edges)
    width_by_count = compute_rank_widths(
        (e.connection_count for e in edge_list), min_width, max_width
    )
    ranked_counts = sorted(width_by_count, reverse=True)
    rank_by_count = {count: i + 1 for i, count in enumerate(ranked_counts)}

    graph = nx.MultiDiGraph()
    for edge in edge_list:
        graph.add_node(edge.src_ip)
        graph.add_node(edge.dst_ip)
        graph.add_edge(
            edge.src_ip,
            edge.dst_ip,
            key=edge.dst_port,
            width=width_by_count[edge.connection_count],
            rank=rank_by_count[edge.connection_count],
            label=edge.label,
            connection_count=edge.connection_count,
            src_port_min=edge.min_src_port,
            src_port_max=edge.max_src_port,
            src_port_range=edge.src_port_range,
            dst_port=edge.dst_port,
            first_seen=edge.first_seen,
            last_seen=edge.last_seen,
            first_seen_text=edge.first_seen_text,
            last_seen_text=edge.last_seen_text,
            protocols=",".join(sorted(edge.protocols)),
            actions=",".join(sorted(edge.actions)),
        )
    return graph
