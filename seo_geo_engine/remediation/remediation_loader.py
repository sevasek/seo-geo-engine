"""
Parses a remediation-plan.md into RemediationItem objects — the
remediation-side twin of checks/standard_loader.py. This is the only place
that reads that table's structure; tests and remediation/plan.py both go
through this loader. Also the only place that WRITES to it (update_status)
— an agent working the queue calls that instead of hand-editing the file.
"""
import re
from dataclasses import dataclass
from pathlib import Path

ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")
VALID_APPROACHES = {"script", "manual"}
VALID_STATUSES = {"not-started", "ready", "in-progress", "applied", "verified"}

_HEADER = ["id", "approach", "depends on", "status", "notes"]


@dataclass
class RemediationItem:
    id: str
    approach: str
    depends_on: str
    status: str
    notes: str
    line_no: int


class RemediationFormatError(ValueError):
    pass


def _split_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def _is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{2,}:?", c) for c in cells)


def load_remediation_plan(path: Path) -> list[RemediationItem]:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    items: list[RemediationItem] = []
    header_cells = None

    for i, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        if not line.startswith("|"):
            continue

        cells = _split_row(line)

        if header_cells is None:
            header_cells = [c.lower() for c in cells]
            if header_cells != _HEADER:
                raise RemediationFormatError(
                    f"{path}:{i}: unexpected table header {cells!r} — expected "
                    f"ID | Approach | Depends on | Status | Notes"
                )
            continue

        if _is_separator_row(cells):
            continue

        if len(cells) != len(header_cells):
            raise RemediationFormatError(
                f"{path}:{i}: row has {len(cells)} cells, expected {len(header_cells)}: {raw_line!r}"
            )

        row_id, approach, depends_on, status, notes = cells

        if not ID_PATTERN.match(row_id):
            raise RemediationFormatError(f"{path}:{i}: {row_id!r} doesn't look like a standard ID (e.g. META-001)")

        if approach not in VALID_APPROACHES:
            raise RemediationFormatError(
                f"{path}:{i}: {row_id} has approach {approach!r}, must be one of {VALID_APPROACHES}"
            )

        if status not in VALID_STATUSES:
            raise RemediationFormatError(
                f"{path}:{i}: {row_id} has status {status!r}, must be one of {VALID_STATUSES}"
            )

        items.append(
            RemediationItem(
                id=row_id,
                approach=approach,
                depends_on=depends_on,
                status=status,
                notes=notes,
                line_no=i,
            )
        )

    if not items:
        raise RemediationFormatError(f"No remediation rows found in {path} — check the table format")

    return items


def load_remediation_plan_by_id(path: Path) -> dict[str, RemediationItem]:
    items = load_remediation_plan(path)
    by_id: dict[str, RemediationItem] = {}
    for item in items:
        if item.id in by_id:
            raise RemediationFormatError(
                f"Duplicate remediation ID {item.id!r} — first seen at line "
                f"{by_id[item.id].line_no}, again at line {item.line_no}"
            )
        by_id[item.id] = item
    return by_id


def update_status(item_id: str, status: str, plan_path: Path, notes: str | None = None) -> None:
    """In-place edit of one row's Status (and optionally Notes) cell — the
    agent-facing alternative to hand-editing remediation-plan.md. Regex-
    targeted at the one line whose first cell is `item_id`, so it can't
    accidentally touch another row."""
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {VALID_STATUSES}, got {status!r}")

    plan_path = Path(plan_path)
    lines = plan_path.read_text(encoding="utf-8").splitlines()

    found = False
    for i, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        cells = _split_row(line)
        if not cells or cells[0] != item_id:
            continue
        if _is_separator_row(cells) or cells[0].lower() == "id":
            continue
        if len(cells) != len(_HEADER):
            continue
        row_id, approach, depends_on, _old_status, old_notes = cells
        new_notes = notes if notes is not None else old_notes
        lines[i] = f"| {row_id} | {approach} | {depends_on} | {status} | {new_notes} |"
        found = True
        break

    if not found:
        raise RemediationFormatError(f"No remediation row for {item_id!r} found in {plan_path}")

    plan_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
