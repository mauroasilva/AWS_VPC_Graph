# AWS VPC Graph

Turn AWS VPC Flow Logs into an interactive connection graph.

- **Nodes** are the IP addresses involved in the traffic.
- **Edges** are directed (source → destination) and one edge is generated
  per destination port between an IP pair.
- **Edge labels** show the observed source-port range (e.g. `21251 - 22353`),
  the destination port, and the first/last seen timestamps.
- **Edge widths** encode a *ranking* of connection counts, not a proportion:
  the edge with the highest number of connections is the widest, the
  second-highest is the second widest, and so on. Equal counts share a width.

New here (or an agent building on this project)? Start with
[docs/PROJECT_AIM.md](docs/PROJECT_AIM.md), then read
[docs/PLAN.md](docs/PLAN.md) and [docs/LESSONS_LEARNED.md](docs/LESSONS_LEARNED.md).

## Installation

```bash
pip install -r requirements.txt        # or: pip install .
```

## Usage

```bash
python -m vpc_graph sample_data/sample_flow_log.txt -o vpc_graph.html
```

Then open `vpc_graph.html` in a browser. The file is self-contained; drag
nodes around, hover edges for full details.

Useful options:

| Option | Effect |
| --- | --- |
| `-o FILE` | Output HTML file (default `vpc_graph.html`) |
| `--graphml FILE` | Also export the graph as GraphML |
| `--action ACCEPT\|REJECT` | Only include records with this action |
| `--min-count N` | Drop edges with fewer than N connections |
| `--fields ...` | Field order for custom log formats |
| `--min-width / --max-width` | Width range used by the rank scale |

Input is the default VPC Flow Log v2 format. Files may contain a header
line with field names (it switches the column order automatically), blank
lines and `#` comments; `NODATA`/`SKIPDATA` records are skipped.

## Development

```bash
python -m unittest discover -s tests
```

Project layout:

```
vpc_graph/
  parser.py         # flow log lines -> FlowRecord
  aggregator.py     # FlowRecords -> ConnectionEdge per (src, dst, dst_port)
  graph_builder.py  # ConnectionEdges -> networkx MultiDiGraph (rank widths)
  renderer.py       # MultiDiGraph -> interactive HTML (pyvis)
  cli.py            # argparse CLI
```
