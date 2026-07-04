"""Parsing of AWS VPC Flow Log records.

Supports the default (version 2) space-separated format:

    version account-id interface-id srcaddr dstaddr srcport dstport
    protocol packets bytes start end action log-status

Custom formats are supported in two ways:

* a header line in the file itself (as produced by CloudWatch Logs Insights
  exports or custom-format logs that include field names), or
* an explicit field list passed to :func:`parse_lines` / :func:`parse_file`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional, Sequence

logger = logging.getLogger(__name__)

#: Field order of the default VPC Flow Log format (version 2).
DEFAULT_FIELDS: tuple[str, ...] = (
    "version",
    "account-id",
    "interface-id",
    "srcaddr",
    "dstaddr",
    "srcport",
    "dstport",
    "protocol",
    "packets",
    "bytes",
    "start",
    "end",
    "action",
    "log-status",
)

#: Fields a record must carry (with non-"-" values) to be usable.
REQUIRED_FIELDS: tuple[str, ...] = (
    "srcaddr",
    "dstaddr",
    "srcport",
    "dstport",
    "start",
    "end",
)

#: log-status values that mean "no flow data in this record".
SKIP_STATUSES = frozenset({"NODATA", "SKIPDATA"})


@dataclass(frozen=True)
class FlowRecord:
    """One usable VPC flow log record (one recorded flow / connection)."""

    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    start: int
    end: int
    action: str


def _looks_like_header(tokens: Sequence[str]) -> bool:
    return "srcaddr" in tokens and "dstaddr" in tokens


def parse_lines(
    lines: Iterable[str],
    fields: Optional[Sequence[str]] = None,
) -> Iterator[FlowRecord]:
    """Yield :class:`FlowRecord` objects from an iterable of log lines.

    Blank lines and ``#`` comments are ignored. A line containing field
    names (e.g. ``srcaddr dstaddr ...``) switches the column order for the
    remainder of the input. Records with ``log-status`` NODATA/SKIPDATA,
    records missing required fields, and malformed lines are skipped with
    a warning.
    """
    field_order = list(fields) if fields else list(DEFAULT_FIELDS)
    for lineno, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        tokens = line.split()
        if _looks_like_header(tokens):
            field_order = tokens
            continue
        record = dict(zip(field_order, tokens))
        if record.get("log-status", "OK") in SKIP_STATUSES:
            continue
        if any(record.get(f, "-") == "-" for f in REQUIRED_FIELDS):
            logger.warning("line %d: skipping record with missing fields", lineno)
            continue
        try:
            yield FlowRecord(
                src_ip=record["srcaddr"],
                dst_ip=record["dstaddr"],
                src_port=int(record["srcport"]),
                dst_port=int(record["dstport"]),
                protocol=record.get("protocol", "-"),
                start=int(record["start"]),
                end=int(record["end"]),
                action=record.get("action", "-"),
            )
        except (KeyError, ValueError) as exc:
            logger.warning("line %d: skipping malformed record (%s)", lineno, exc)


def parse_file(
    path: str | Path,
    fields: Optional[Sequence[str]] = None,
) -> Iterator[FlowRecord]:
    """Yield :class:`FlowRecord` objects from a flow log file."""
    with open(path, "r", encoding="utf-8") as handle:
        yield from parse_lines(handle, fields=fields)
