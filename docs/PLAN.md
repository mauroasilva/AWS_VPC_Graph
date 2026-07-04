# Implementation Plan

Plan for the AWS VPC connection-graph application delivered in this
repository. See [PROJECT_AIM.md](PROJECT_AIM.md) for the requirements this
plan implements.

## Overview

A four-stage pipeline, each stage a separate module so it can be replaced
or extended independently:

```
flow log file(s)
      |
      v
 parser.py        lines -> FlowRecord (src/dst IP+port, protocol, start, end, action)
      |
      v
 aggregator.py    FlowRecords -> ConnectionEdge per (src_ip, dst_ip, dst_port):
      |             count, min/max src port, first/last seen, protocols, actions
      v
 graph_builder.py ConnectionEdges -> networkx.MultiDiGraph:
      |             IP nodes; edge key = dst_port; width from count *ranking*
      v
 renderer.py      MultiDiGraph -> self-contained interactive HTML (pyvis/vis.js)
```

`cli.py` (exposed as `python -m vpc_graph` and the `vpc-graph` console
script) wires the stages together.

## Stage details

### 1. Parsing (`vpc_graph/parser.py`)
- Accepts the default VPC Flow Log **version 2** space-separated format:
  `version account-id interface-id srcaddr dstaddr srcport dstport
  protocol packets bytes start end action log-status`.
- Custom formats via an in-file header line (a line containing field
  names such as `srcaddr dstaddr ...`) or the `--fields` CLI option.
- Skips blank lines, `#` comments, `NODATA`/`SKIPDATA` records, records
  with `-` in required fields, and malformed lines (with a `logging`
  warning) instead of aborting the whole run.
- Streams records as a generator, so file size is not a memory concern
  at this stage.

### 2. Aggregation (`vpc_graph/aggregator.py`)
- Edge identity: `(src_ip, dst_ip, dst_port)` — directional, one edge per
  destination port, as required.
- Each flow log record counts as **one connection** for its edge.
- Tracked per edge: connection count, min/max source port, min `start` /
  max `end` timestamps, set of protocols, set of actions.
- Label format (one edge label, four lines):
  ```
  src ports: 21251 - 22353
  dst port: 22
  first: 2014-12-14 04:06:50Z
  last: 2014-12-14 04:57:50Z
  ```
  A single observed source port is shown as just the port number.
- Optional filter on `action` (ACCEPT/REJECT); default includes both.

### 3. Graph building (`vpc_graph/graph_builder.py`)
- `networkx.MultiDiGraph`; nodes are IP strings; parallel edges between
  the same IP pair are keyed by destination port.
- **Rank-based widths:** distinct connection counts are sorted
  descending and mapped to evenly spaced widths between `--max-width`
  (default 10, rank 1) and `--min-width` (default 1, lowest rank).
  Equal counts share a rank and therefore a width (dense ranking). The
  spacing depends only on the number of distinct counts, never on the
  magnitude of the counts — this satisfies the "ranking, not
  proportional" requirement.
- All aggregate values are stored as edge attributes (`connection_count`,
  `rank`, `src_port_min/max`, `first_seen`, `last_seen`, `protocols`,
  `actions`, ...), so alternative renderers or exports need nothing but
  the graph object.

### 4. Rendering (`vpc_graph/renderer.py`)
- pyvis/vis.js interactive HTML, written with `cdn_resources="in_line"`
  so the output is a single self-contained file.
- Directed arrows, multi-line edge labels, and a hover tooltip per edge
  with the full detail (count, rank, ports, protocols, actions,
  timestamps).
- Optional GraphML export (`--graphml`) for programmatic consumers.

## Testing & verification

- Unit tests (stdlib `unittest`, no extra dependency) in `tests/` cover:
  parsing (formats, skip rules), aggregation (port range label incl. the
  exact example from the requirements, first/last seen, per-dst-port
  edges, direction), and ranking (rank vs. magnitude, ties, edge cases).
  Run with `python -m unittest discover -s tests`.
- End-to-end verification: run the CLI against
  `sample_data/sample_flow_log.txt` and open the HTML output in a
  browser. The sample exercises the requirement example (source ports
  21251/22022/22353 → label `21251 - 22353`), multiple destination
  ports, both directions between a pair, REJECT traffic and
  NODATA/SKIPDATA records.

## Dependencies

Python ≥ 3.9, `networkx`, `pyvis` (see `requirements.txt` /
`pyproject.toml`). Everything else is standard library.
