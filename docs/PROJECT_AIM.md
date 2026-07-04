# Project Aim

> **Read this first.** This file is the entry point for anyone (human or
> agent) working on this repository. It states what the project is for and
> the requirements every change must keep satisfying. See
> [PLAN.md](PLAN.md) for the architecture and
> [LESSONS_LEARNED.md](LESSONS_LEARNED.md) for the decision log and notes
> for future agents.

## Aim

Build a Python application that processes **AWS VPC Flow Logs** and
produces a **graph of the network connections** they describe, so that the
traffic between hosts can be inspected visually.

## Core requirements (must always hold)

1. **Nodes are IP addresses** — every IP that appears as a source or
   destination in the logs becomes a node.
2. **One edge per destination port** — traffic from IP A to IP B is split
   into one edge for each destination port observed (A→B:22 and A→B:443
   are two distinct edges).
3. **Edge labels** state:
   - the range of observed *source* ports, formatted `min - max`
     (e.g. source ports 21251, 22022 and 22353 → label `21251 - 22353`);
   - the destination port;
   - the first-seen and last-seen timestamps of the aggregated flows.
4. **Edge width is a ranking, not a proportion.** The edge with the
   highest connection count gets the largest width, the second-highest
   count the second-largest width, and so on. The widths must NOT be
   proportional to the raw counts — an edge with 1000 connections is one
   rank above an edge with 3 connections, not 300× wider.

## Current implementation (v0.2.0)

A `vpc_graph` Python package with a CLI:

```bash
python -m vpc_graph <flow-log-file-or-folder> -o vpc_graph.html
```

Inputs can be plain log files or folder trees laid out as
`<vpc-id>/<year>/<month>/<day>/*.log` (each day folder holding many
minute-chunk `.log` files). It parses flow log records, aggregates them
into `(src_ip, dst_ip, dst_port)` edges, builds a
`networkx.MultiDiGraph` with rank-based widths, and renders a
self-contained interactive HTML page (pyvis/vis.js). Sample inputs live
in `sample_data/` (single file and folder tree); unit tests live in
`tests/`.
