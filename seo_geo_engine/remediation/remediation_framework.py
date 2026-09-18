"""
The registry that ties a standard row currently failing or blocked to the
code (or documented procedure) that fixes it — the remediation-side twin of
checks/framework.py's @check registry.

Every remediation is registered with @remediate("SOME-ID"). Decorating twice
with the same ID is a hard error at import time, same reasoning as
@check: one standard row gets one remediation, not two competing fixes —
except a profile may overwrite an engine default (origin="engine" →
origin="profile"). Two engine handlers for the same ID, or two profile
handlers for the same ID, remain a hard error. See
docs/design/engine-owned-remediation.md.

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
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal

from seo_geo_engine.paths import engine_playbooks_dir

REGISTRY: dict[str, "RegisteredRemediation"] = {}

VALID_KINDS = {"script", "manual"}
VALID_ORIGINS = {"engine", "profile"}

# import_profile_code() sets this to "profile" while the profile's
# handlers_module is imported, so a re-registration of an engine ID is an
# override rather than a duplicate. Engine modules leave it at "engine".
registration_origin: ContextVar[str] = ContextVar("remediation_origin", default="engine")


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
    origin: Literal["engine", "profile"] = "engine"
    # Default "Depends on" cell when plan-sync appends a row for this ID.
    # "—" means ready to work; anything else parks the item in the blocked
    # section of the queue. Never inferred from the ID string.
    depends_on: str = "—"


def _register(entry: RegisteredRemediation) -> None:
    existing = REGISTRY.get(entry.id)
    if existing is None:
        REGISTRY[entry.id] = entry
        return
    if existing.origin == "engine" and entry.origin == "profile":
        REGISTRY[entry.id] = entry
        return
    raise ValueError(
        f"Duplicate remediation for {entry.id}: {entry.fn.__name__} conflicts with "
        f"already-registered {existing.fn.__name__} (origin={existing.origin!r}). "
        f"One standard row gets one remediation; a profile may overwrite an engine "
        f"default, but two engine or two profile handlers for the same ID is an error."
    )


def remediate(standard_id: str, *, kind: str, depends_on: str = "—"):
    """Decorator: register fn as the remediation for standard row `standard_id`."""
    if kind not in VALID_KINDS:
        raise ValueError(f"{standard_id}: kind must be one of {VALID_KINDS}, got {kind!r}")

    def decorator(fn):
        origin = registration_origin.get()
        _register(
            RegisteredRemediation(
                id=standard_id,
                kind=kind,
                fn=fn,
                origin=origin,
                depends_on=depends_on,
            )
        )
        return fn

    return decorator


def manual(standard_id: str, playbook: str, *, depends_on: str = "CMS-ACCESS"):
    """
    Register `standard_id` as a manual remediation whose procedure lives in
    `playbook` (a path, e.g. "playbooks/TRUST-001.md"). Mirrors the
    read-only-stub shape of checks.framework.blocked() — the actual content
    lives in one place (the playbook file), not duplicated into the
    registry.
    """
    origin = registration_origin.get()

    def fn(site: dict) -> RemediationResult:
        return RemediationResult(id=standard_id, kind="manual", detail=f"See {playbook}")

    fn.__name__ = f"manual_{standard_id.replace('-', '_')}"
    _register(
        RegisteredRemediation(
            id=standard_id,
            kind="manual",
            fn=fn,
            playbook=playbook,
            origin=origin,
            depends_on=depends_on,
        )
    )
    return fn


def playbook_path(registered: RegisteredRemediation, profile_root: Path | None = None) -> Path:
    """Resolve a manual playbook file. Engine playbooks live under the
    packaged `seo_geo_engine/remediation/` tree; profile playbooks resolve
    against the profile directory."""
    rel = Path(registered.playbook)
    if registered.origin == "engine":
        # Engine manuals store "playbooks/<ID>.md"; the file lives next to
        # this package's other shipped remediations.
        return engine_playbooks_dir() / rel.name
    if profile_root is None:
        raise ValueError(f"{registered.id}: profile-origin playbook requires profile_root")
    return Path(profile_root) / rel
