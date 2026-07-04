"""Render the connection graph as an interactive HTML page (pyvis/vis.js).

The generated file is fully self-contained (JS/CSS inlined) and can be
opened directly in a browser.
"""

from __future__ import annotations

import json
from pathlib import Path

import networkx as nx
from pyvis.network import Network

_OPTIONS = {
    "edges": {
        "arrows": {"to": {"enabled": True, "scaleFactor": 0.6}},
        "font": {"size": 9, "align": "middle"},
        "smooth": {"enabled": True, "type": "dynamic"},
    },
    "nodes": {
        "shape": "dot",
        "size": 14,
        "font": {"size": 13},
    },
    "physics": {
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {"gravitationalConstant": -80, "springLength": 220},
        "stabilization": {"iterations": 200},
    },
    "interaction": {"hover": True, "tooltipDelay": 120},
}


def _edge_tooltip(data: dict) -> str:
    return (
        f"connections: {data['connection_count']} (rank {data['rank']})\n"
        f"src ports: {data['src_port_range']}\n"
        f"dst port: {data['dst_port']}\n"
        f"protocols: {data['protocols']}\n"
        f"actions: {data['actions']}\n"
        f"first seen: {data['first_seen_text']}\n"
        f"last seen: {data['last_seen_text']}"
    )


def render_html(graph: nx.MultiDiGraph, output_path: str | Path) -> Path:
    """Write the interactive visualisation to ``output_path`` and return it."""
    net = Network(
        height="900px",
        width="100%",
        directed=True,
        cdn_resources="in_line",
    )
    net.set_options(json.dumps({"physics": _OPTIONS["physics"],
                                "edges": _OPTIONS["edges"],
                                "nodes": _OPTIONS["nodes"],
                                "interaction": _OPTIONS["interaction"]}))

    for node in graph.nodes:
        degree = graph.degree(node)
        net.add_node(node, label=node, title=f"{node}\nedges: {degree}")

    for src, dst, _key, data in graph.edges(keys=True, data=True):
        net.add_edge(
            src,
            dst,
            width=data["width"],
            label=data["label"],
            title=_edge_tooltip(data),
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    net.write_html(str(output_path), notebook=False, open_browser=False)
    return output_path
