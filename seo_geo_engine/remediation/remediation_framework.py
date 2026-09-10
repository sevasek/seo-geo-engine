"""
The registry that ties a standard row currently failing or blocked to the
code (or documented procedure) that fixes it — the remediation-side twin of
checks/framework.py's @check registry.

Every remediation is registered with @remediate("SOME-ID"). Decorating twice
with the same ID is a hard error at import time, same reasoning as
@check: one standard row gets one remediation, not two competing fixes.

A remediation is one of two kinds:

- `script` — a callable that can actually compute the fix's content from
  crawl data today (e.g. a structured-data snippet built from already-known
  facts). It never publishes anything — no engine or profile is assumed to
  have CMS write access — so its job is to produce a ready-to-paste artifact
  a human applies, not to mutate the live site.
- `manual` — a stub pointing at a written playbook, for fixes that are
  fundamentally editorial, relational, or access-gated (CMS content edits,
  photography, external listings, granted API access) rather than
  mechanically generatable.

A remediation function's signature is always:

    def remediate_xxx(site: dict) -> RemediationResult

`site` is the same crawled dataset shape @check functions receive (profile
merged in as site["profile"], same as checks).
"""
from dataclasses import dataclass, field
from typing import Callable

REGISTRY: dict[str, "RegisteredRemediation"] = {}

VALID_KINDS = {"script", "manual"}


@dataclass
class RemediationResult:
    id: str
    kind: str  # "script" | "manual"
    detail: str = ""
    # For kind="script": the concrete, ready-to-paste fix content (a JSON-LD
    # block, an exact old->new URL swap, etc). Empty for kind="manual" —
    # the playbook file is the artifact there.
    artifact: str = ""
    evidence: list = field(default_factory=list)

    def __post_init__(self):
        if self.kind not in VALID_KINDS:
            raise ValueError(f"{self.id}: kind must be one of {VALID_KINDS}, got {self.kind!r}")
        if self.kind == "manual" and self.artifact:
            raise ValueError(f"{self.id}: manual remediations don't set artifact — the playbook file is the artifact")


@dataclass
class RegisteredRemediation:
    id: str
    kind: str
    fn: Callable[[dict], RemediationResult]
    playbook: str = ""  # relative path, set for kind="manual" entries


def remediate(standard_id: str, *, kind: str):
    """Decorator: register fn as the remediation for standard row `standard_id`."""
    if kind not in VALID_KINDS:
        raise ValueError(f"{standard_id}: kind must be one of {VALID_KINDS}, got {kind!r}")

    def decorator(fn):
        if standard_id in REGISTRY:
            existing = REGISTRY[standard_id].fn.__name__
            raise ValueError(
                f"Duplicate remediation for {standard_id}: {fn.__name__} conflicts with "
                f"already-registered {existing}. One standard row gets one remediation."
            )
        REGISTRY[standard_id] = RegisteredRemediation(id=standard_id, kind=kind, fn=fn)
        return fn

    return decorator


def manual(standard_id: str, playbook: str):
    """
    Register `standard_id` as a manual remediation whose procedure lives in
    `playbook` (a path, e.g. "playbooks/TRUST-001.md"). Mirrors the
    read-only-stub shape of checks.framework.blocked() — the actual content
    lives in one place (the playbook file), not duplicated into the
    registry.
    """

    def fn(site: dict) -> RemediationResult:
        return RemediationResult(id=standard_id, kind="manual", detail=f"See {playbook}")

    if standard_id in REGISTRY:
        existing = REGISTRY[standard_id].fn.__name__
        raise ValueError(
            f"Duplicate remediation for {standard_id}: manual({standard_id!r}, ...) conflicts with "
            f"already-registered {existing}. One standard row gets one remediation."
        )
    fn.__name__ = f"manual_{standard_id.replace('-', '_')}"
    REGISTRY[standard_id] = RegisteredRemediation(id=standard_id, kind="manual", fn=fn, playbook=playbook)
