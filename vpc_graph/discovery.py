"""Discovery of flow log files in a date-partitioned folder tree.

Expected layout::

    <root>/<vpc-id>/<year>/<month>/<day>/<chunk>.log

where each day folder contains multiple ``.log`` files (minute chunks of
that day). All chunks found are returned so they can be parsed and
aggregated together.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

logger = logging.getLogger(__name__)


def _valid_date_parts(year: str, month: str, day: str) -> bool:
    if not (year.isdigit() and month.isdigit() and day.isdigit()):
        return False
    return (
        len(year) == 4
        and 1 <= int(month) <= 12
        and 1 <= int(day) <= 31
    )


def discover_log_files(root: str | Path) -> List[Path]:
    """Return all ``.log`` files under ``root`` matching the
    ``<vpc-id>/<year>/<month>/<day>/*.log`` layout, sorted by path
    (i.e. by VPC, then chronologically, then by chunk name).

    Files whose year/month/day folders are not plausible dates are
    skipped with a warning, as are ``.log`` files at any other depth.
    """
    root = Path(root)
    found: List[Path] = []
    for path in sorted(root.glob("*/*/*/*/*.log")):
        if not path.is_file():
            continue
        _vpc_id, year, month, day = path.relative_to(root).parts[:4]
        if not _valid_date_parts(year, month, day):
            logger.warning(
                "skipping %s: expected <vpc-id>/<year>/<month>/<day>/ layout", path
            )
            continue
        found.append(path)

    misplaced = sorted(set(root.rglob("*.log")) - set(found))
    for path in misplaced:
        if path.is_file():
            logger.warning(
                "skipping %s: not at <vpc-id>/<year>/<month>/<day>/ depth", path
            )
    return found


def expand_inputs(paths: Iterable[str | Path]) -> List[Path]:
    """Expand a mix of file and folder arguments into a list of log files.

    Files are passed through as-is; folders are searched with
    :func:`discover_log_files`.
    """
    expanded: List[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            logs = discover_log_files(path)
            if not logs:
                logger.warning(
                    "no log files found under %s "
                    "(expected <vpc-id>/<year>/<month>/<day>/*.log)",
                    path,
                )
            expanded.extend(logs)
        else:
            expanded.append(path)
    return expanded
