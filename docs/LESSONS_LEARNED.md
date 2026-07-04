# Lessons Learned & Decision Log

This file records every decision made while building v0.1.0, notes for
future agents, and known limitations. Read
[PROJECT_AIM.md](PROJECT_AIM.md) first for the requirements and
[PLAN.md](PLAN.md) for the architecture.

## Decisions that needed human input

The initial build ran **fully autonomously** — no human was available
mid-task, so none of the decisions below actually received human input.
They are listed here because they are interpretation calls a human may
want to revisit; each was resolved with the stated default. If any
default is wrong, the "where to change it" pointer shows the single place
to fix.

| # | Question | Default chosen | Where to change it |
|---|----------|----------------|--------------------|
| 1 | What is "one connection", given that VPC Flow Logs record *aggregated flows*, not individual TCP connections? | Each usable flow log record counts as one connection. | `ConnectionEdge.add()` in `vpc_graph/aggregator.py` |
| 2 | Should the edge identity include the protocol (TCP 53 vs UDP 53)? The requirement only says "an edge for each destination port". | Key is `(src_ip, dst_ip, dst_port)` only; protocols are merged into an edge attribute. | `EdgeKey` / `aggregate()` in `vpc_graph/aggregator.py` |
| 3 | Is the width ranking global or per node pair? | Global across all edges in the graph. | `build_graph()` in `vpc_graph/graph_builder.py` |
| 4 | How should ties in connection count be ranked? | Dense ranking: equal counts share one rank and one width. | `compute_rank_widths()` in `vpc_graph/graph_builder.py` |
| 5 | Should REJECTed traffic appear in the graph? | Yes by default (useful for security analysis); `--action ACCEPT` filters it out. | `--action` default in `vpc_graph/cli.py` |
| 6 | Label when only one source port was seen — `21251` or `21251 - 21251`? | Just `21251`. | `ConnectionEdge.src_port_range` in `vpc_graph/aggregator.py` |
| 7 | Output medium? | Interactive self-contained HTML (pyvis), because edge labels/tooltips and dragging matter for inspection; optional GraphML export for tooling. | `vpc_graph/renderer.py`, `--graphml` in `cli.py` |

## Decisions made automatically

- **Language/stack:** Python 3 (≥3.9), `networkx` for the graph model,
  `pyvis` (vis.js) for rendering. Both are widespread and keep the code
  small.
- **Architecture:** four independent pipeline stages (parse → aggregate →
  build graph → render) so each can be swapped without touching the rest.
- **Width scale:** ranks are mapped to widths evenly spaced between
  `--min-width` (1.0) and `--max-width` (10.0); highest count = widest.
  Spacing is by rank position only — deliberately independent of count
  magnitude, per the requirement.
- **Timestamps:** flow log `start`/`end` are Unix epoch seconds; first
  seen = min(`start`), last seen = max(`end`) over the edge's records;
  displayed as UTC (`YYYY-MM-DD HH:MM:SSZ`). Raw epoch values are also
  kept as edge attributes.
- **Input robustness:** default v2 field order; a header line inside the
  file switches the column order; `--fields` overrides it entirely.
  `NODATA`/`SKIPDATA` records, `-` values in required fields, comments,
  blank lines and malformed lines are skipped (warning logged) instead of
  failing the run.
- **Direction is preserved:** A→B and B→A are different edges
  (`MultiDiGraph`), matching how flow logs report each direction as its
  own flow.
- **Edge label layout:** four short lines (src ports / dst port / first /
  last) rather than one long line, to stay legible on the canvas; the
  hover tooltip additionally shows count, rank, protocols and actions.
- **Tests:** stdlib `unittest` (no test-framework dependency). 23 tests,
  including the literal example from the requirements (21251/22022/22353
  → `21251 - 22353`).
- **Sample data:** synthetic `sample_data/sample_flow_log.txt` using the
  documented AWS example format, covering every parser/aggregator branch.

## Notes for future agents

- **Start at `docs/PROJECT_AIM.md`** — it lists the invariants every
  change must keep. The requirement example (ports 21251/22022/22353) is
  encoded as a unit test; keep it passing.
- **Data flow:** `parse_file()` yields `FlowRecord`s → `aggregate()`
  returns `{(src, dst, dst_port): ConnectionEdge}` → `build_graph()`
  returns a `networkx.MultiDiGraph` whose edge key is the destination
  port → `render_html()` writes the page. To add a new output format,
  consume the `MultiDiGraph` — every aggregate value is already an edge
  attribute, so no other module needs changes.
- **Verification recipe:** `python -m unittest discover -s tests`, then
  `python -m vpc_graph sample_data/sample_flow_log.txt -o /tmp/g.html`
  and open it in a browser (a headless-Chromium screenshot works; the
  page logs no JS errors). Expected sample output: 6 nodes, 5 edges,
  15 connections, widths 1.0 / 3.25 / 5.5 / 7.75 / 10.0.
- **pyvis quirks (0.3.2):** use `write_html(path, notebook=False)` —
  `show()` assumes a notebook template. `cdn_resources="in_line"` makes
  the HTML self-contained; the default (`local`) drops a `lib/` folder
  next to the output. Options must be passed to `set_options()` as a JSON
  string. vis.js supports `\n` in edge labels natively.
- **Scaling caution:** every edge carries a 4-line label; on graphs with
  hundreds of edges the canvas gets crowded. Sensible next steps if that
  becomes a problem: a `--no-labels` flag (tooltips already carry all the
  info), `--min-count` (already exists) to prune noise, or clustering by
  subnet.
- **Known limitations (deliberate v0.1.0 scope):** no direct S3/CloudWatch
  ingestion (feed it text files); no protocol-number→name translation
  (edges show `6`, not `TCP`); IPv6 addresses pass through untested but
  the parser has no IPv4 assumptions; gzip files must be decompressed
  first.
- The `docs/` files are part of the deliverable — when you change
  behaviour, update PROJECT_AIM.md (if invariants move), PLAN.md (if the
  architecture moves) and append your decisions here.
