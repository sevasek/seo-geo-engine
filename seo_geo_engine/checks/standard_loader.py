"""
Parses one or more standard/*.md files into StandardItem objects and merges
them into a single effective standard. This is the only place that reads the
markdown table structure — everything else (tests, report generator) goes
through this loader, so the table format only needs to be right in one place.

A profile's own standard/extensions.md is just another file in the same
format, merged in after the engine's shipped defaults — see
merge_standards()/load_standard() below and profile.py's
effective_standard().
"""
import re
from dataclasses import dataclass
from pathlib import Path

ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")
VALID_STATUSES = {"open", "blocked"}

MIN_WEIGHT = 1
MAX_WEIGHT = 5


@dataclass
class StandardItem:
    id: str
    category: str
    rule: str
    source: str
    weight: int
    status: str
    unblock_requirement: str
    line_no: int
    origin: str = ""  # which file this row was parsed from — useful for error messages


class StandardFormatError(ValueError):
    pass


def _split_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def _is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{2,}:?", c) for c in cells)


def _parse_one_file(path: Path) -> list[StandardItem]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    items: list[StandardItem] = []
    current_category = None
    header_cells = None

    for i, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        if line.startswith("## "):
            current_category = line[3:].strip()
            header_cells = None
            continue

        if not line.startswith("|"):
            continue

        cells = _split_row(line)

        if header_cells is None:
            header_cells = [c.lower() for c in cells]
            if header_cells != ["id", "rule", "source", "weight", "status", "unblock requirement"]:
                raise StandardFormatError(
                    f"{path}:{i}: unexpected table header {cells!r} under category "
                    f"{current_category!r} — expected ID | Rule | Source | Weight | Status | Unblock requirement"
                )
            continue

        if _is_separator_row(cells):
            continue

        if len(cells) != len(header_cells):
            raise StandardFormatError(
                f"{path}:{i}: row has {len(cells)} cells, expected {len(header_cells)}: {raw_line!r}"
            )

        row_id, rule, source, weight_str, status, unblock = cells

        if not ID_PATTERN.match(row_id):
            raise StandardFormatError(f"{path}:{i}: {row_id!r} doesn't look like a standard ID (e.g. META-001)")

        if status not in VALID_STATUSES:
            raise StandardFormatError(
                f"{path}:{i}: {row_id} has status {status!r}, must be one of {VALID_STATUSES}"
            )

        if not weight_str.isdigit() or not (MIN_WEIGHT <= int(weight_str) <= MAX_WEIGHT):
            raise StandardFormatError(
                f"{path}:{i}: {row_id} has weight {weight_str!r}, must be an integer "
                f"{MIN_WEIGHT}-{MAX_WEIGHT}"
            )

        items.append(
            StandardItem(
                id=row_id,
                category=current_category or "Uncategorized",
                rule=rule,
                source=source,
                weight=int(weight_str),
                status=status,
                unblock_requirement=unblock,
                line_no=i,
                origin=str(path),
            )
        )

    # No "must have at least one row" guard here: a profile's own
    # extensions.md is legitimately empty until its first real rule is
    # added (see scaffold/init_profile.py) — a malformed header or row
    # shape is still caught above, which is the actual authoring-mistake
    # case worth failing loudly on.
    return items


def merge_standards(paths: list[Path]) -> list[StandardItem]:
    """Parse each path in order and merge by ID — a later file's row with the
    same ID replaces an earlier one entirely (reweight/reword/change status),
    same mental model as a CSS cascade. Order of first appearance is kept so
    the rendered report's row order stays stable across a profile adding
    rows next to related ones instead of always at the bottom."""
    by_id: dict[str, StandardItem] = {}
    order: list[str] = []
    for path in paths:
        for item in _parse_one_file(path):  # still hard-errors on a dup ID *within* one file (see load_standard_by_id)
            if item.id not in by_id:
                order.append(item.id)
            by_id[item.id] = item
    return [by_id[i] for i in order]


def load_standard(paths: Path | list[Path] | None) -> list[StandardItem]:
    if paths is None:
        raise ValueError("load_standard() needs at least one standard.md path — pass the engine's shipped defaults")
    if isinstance(paths, (str, Path)):
        paths = [Path(paths)]
    else:
        paths = [Path(p) for p in paths]
    return merge_standards(paths)


def load_standard_by_id(paths: Path | list[Path] | None) -> dict[str, StandardItem]:
    """Same as load_standard() but also guards against a single FILE
    declaring the same ID twice (a real authoring mistake, distinct from one
    file intentionally overriding another)."""
    seen_in_file: dict[str, set[str]] = {}
    items = load_standard(paths)
    for item in items:
        seen_in_file.setdefault(item.origin, set())
    # Re-parse per file to catch intra-file duplicates specifically.
    file_list = [Path(paths)] if isinstance(paths, (str, Path)) else [Path(p) for p in paths]
    for path in file_list:
        ids_here: dict[str, int] = {}
        for item in _parse_one_file(path):
            if item.id in ids_here:
                raise StandardFormatError(
                    f"Duplicate standard ID {item.id!r} within {path} — first seen at line "
                    f"{ids_here[item.id]}, again at line {item.line_no}"
                )
            ids_here[item.id] = item.line_no
    return {item.id: item for item in items}
