"""Aggregation of flow records into graph edges.

Each edge is identified by ``(src_ip, dst_ip, dst_port)`` - i.e. one edge is
generated per destination port between a pair of IPs. All records matching
the key are folded into a single :class:`ConnectionEdge` carrying the
connection count, the observed source-port range and first/last seen
timestamps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional, Tuple

from vpc_graph.parser import FlowRecord

EdgeKey = Tuple[str, str, int]


def format_timestamp(epoch_seconds: int) -> str:
    """Render a Unix timestamp as a compact UTC string."""
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%SZ"
    )


@dataclass
class ConnectionEdge:
    """Aggregated traffic between two IPs towards one destination port."""

    src_ip: str
    dst_ip: str
    dst_port: int
    connection_count: int = 0
    min_src_port: Optional[int] = None
    max_src_port: Optional[int] = None
    first_seen: Optional[int] = None
    last_seen: Optional[int] = None
    protocols: set = field(default_factory=set)
    actions: set = field(default_factory=set)

    def add(self, record: FlowRecord) -> None:
        self.connection_count += 1
        if self.min_src_port is None or record.src_port < self.min_src_port:
            self.min_src_port = record.src_port
        if self.max_src_port is None or record.src_port > self.max_src_port:
            self.max_src_port = record.src_port
        if self.first_seen is None or record.start < self.first_seen:
            self.first_seen = record.start
        if self.last_seen is None or record.end > self.last_seen:
            self.last_seen = record.end
        self.protocols.add(record.protocol)
        self.actions.add(record.action)

    @property
    def src_port_range(self) -> str:
        """Source-port range label, e.g. ``21251 - 22353`` (or ``21251``
        when only a single source port was observed)."""
        if self.min_src_port == self.max_src_port:
            return str(self.min_src_port)
        return f"{self.min_src_port} - {self.max_src_port}"

    @property
    def first_seen_text(self) -> str:
        return format_timestamp(self.first_seen)

    @property
    def last_seen_text(self) -> str:
        return format_timestamp(self.last_seen)

    @property
    def label(self) -> str:
        """Multi-line edge label: source-port range, destination port and
        first/last seen timestamps."""
        return (
            f"src ports: {self.src_port_range}\n"
            f"dst port: {self.dst_port}\n"
            f"first: {self.first_seen_text}\n"
            f"last: {self.last_seen_text}"
        )


def aggregate(
    records: Iterable[FlowRecord],
    action: Optional[str] = None,
) -> Dict[EdgeKey, ConnectionEdge]:
    """Fold flow records into edges keyed by ``(src_ip, dst_ip, dst_port)``.

    ``action`` optionally restricts aggregation to records with a matching
    action (``ACCEPT`` or ``REJECT``); by default all records are included.
    """
    edges: Dict[EdgeKey, ConnectionEdge] = {}
    for record in records:
        if action is not None and record.action != action:
            continue
        key: EdgeKey = (record.src_ip, record.dst_ip, record.dst_port)
        edge = edges.get(key)
        if edge is None:
            edge = ConnectionEdge(
                src_ip=record.src_ip,
                dst_ip=record.dst_ip,
                dst_port=record.dst_port,
            )
            edges[key] = edge
        edge.add(record)
    return edges
