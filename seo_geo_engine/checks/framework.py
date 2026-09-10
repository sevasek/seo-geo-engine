"""
The registry that ties a standard row (built-in or profile-added) to the code
that checks it.

Every check function is decorated with @check("SOME-ID"). Decorating twice
with the same ID is a hard error at import time — two functions can't both
claim to be the assessment for one standard row, that ambiguity is exactly
what the traceability tests exist to catch, so fail as loud as possible.

A check function's signature is always:

    def check_xxx(site: dict) -> CheckResult

`site` is the crawled dataset shape produced by the crawler (live or
local-serve): {"pages": [...], "sitemapUrls": [...], "profile": {...}, ...}.
`site["profile"]` is the loaded SiteProfile's data (see profile.py), merged
in by report.run_report() before any check runs — this is how a profile's
site-specific facts (base URL, entity clusters, contact patterns, ...) reach
a check without changing this function signature. A check looks at as many
or as few pages/profile fields as it needs and returns exactly ONE
CheckResult summarizing the whole site against that one rule — this is what
keeps "one standard row -> one report row" true without extra bookkeeping.
"""
from dataclasses import dataclass, field
from typing import Callable

REGISTRY: dict[str, "RegisteredCheck"] = {}


@dataclass
class CheckResult:
    id: str
    verdict: str  # "pass" | "fail" | "partial" | "blocked"
    detail: str = ""
    evidence: list = field(default_factory=list)
    # How much of the rule is actually satisfied, 0.0-1.0 — e.g. 16/19 pages
    # compliant -> 0.842. Drives partial-credit scoring in report.py; None
    # for blocked results, which never contribute to the scored numerator
    # regardless of this field.
    fraction: float | None = None

    def __post_init__(self):
        valid = {"pass", "fail", "partial", "blocked"}
        if self.verdict not in valid:
            raise ValueError(f"{self.id}: verdict must be one of {valid}, got {self.verdict!r}")
        if self.fraction is not None and not (0.0 <= self.fraction <= 1.0):
            raise ValueError(f"{self.id}: fraction must be 0.0-1.0, got {self.fraction!r}")
        if self.verdict == "blocked" and self.fraction is not None:
            raise ValueError(f"{self.id}: blocked results must not set fraction (always scores 0)")


@dataclass
class RegisteredCheck:
    id: str
    fn: Callable[[dict], CheckResult]


def check(standard_id: str):
    """Decorator: register fn as the assessment for standard row `standard_id`."""

    def decorator(fn):
        if standard_id in REGISTRY:
            existing = REGISTRY[standard_id].fn.__name__
            raise ValueError(
                f"Duplicate check for {standard_id}: {fn.__name__} conflicts with "
                f"already-registered {existing}. One standard row gets one check function."
            )
        REGISTRY[standard_id] = RegisteredCheck(id=standard_id, fn=fn)
        return fn

    return decorator


def blocked(standard_id: str) -> CheckResult:
    """
    A stub result for a standard row that can't be assessed yet. Leave
    `detail` empty — the report generator fills it in from the standard
    doc's "unblock requirement" column, so that text has one home, not two.
    """
    return CheckResult(id=standard_id, verdict="blocked", detail="")


def passed(standard_id: str, detail: str = "", evidence: list | None = None, fraction: float = 1.0) -> CheckResult:
    return CheckResult(id=standard_id, verdict="pass", detail=detail, evidence=evidence or [], fraction=fraction)


def failed(standard_id: str, detail: str = "", evidence: list | None = None, fraction: float = 0.0) -> CheckResult:
    """
    `fraction` defaults to 0.0 (nothing complies) but should be set to the
    actual compliant proportion whenever the check can compute one — e.g.
    "16/19 pages fail" -> 3/19 pages *do* comply -> fraction=3/19. That's
    what makes the score partial-credit instead of all-or-nothing per rule.
    """
    return CheckResult(id=standard_id, verdict="fail", detail=detail, evidence=evidence or [], fraction=fraction)


def partial(standard_id: str, detail: str = "", evidence: list | None = None, fraction: float = 0.5) -> CheckResult:
    return CheckResult(id=standard_id, verdict="partial", detail=detail, evidence=evidence or [], fraction=fraction)
