# Scheduled routine: review and merge {{ORG_NAME}} SEO/GEO PRs

Runs on a schedule against this profile's repo. Re-read this profile's
`CLAUDE.md`/`README.md` fresh each run (don't rely on a stale memory of
them) before reviewing anything.

For each open PR:

1. Run `pytest` against the PR's branch. A red suite is an automatic
   request-changes — don't evaluate content quality until it's green.
2. If the PR changes `standard/extensions.md` or `checks_ext.py`,
   regenerate the report from the PR's branch and diff it against what the
   PR claims changed — a mismatch (report doesn't move the way the PR
   describes) is worth a comment even if tests pass.
3. If the PR changes `remediation-plan.md` or `handlers.py`, confirm every
   non-passing standard item still has exactly one row and one registered
   handler (the traceability tests should already enforce this, but a
   `pytest` bypass or `--no-verify` commit wouldn't have been checked).
4. Check the PR body states what changed, why, and what was verified — a
   PR with no rationale is worth a comment asking for one before merging,
   not a silent approval.
5. Anything requiring business/compliance/editorial judgment this routine
   can't make on its own: leave a comment describing exactly what's needed,
   don't guess and don't block indefinitely either.
6. Approve and squash-merge if all of the above check out. Never merge your
   own PR (this routine shouldn't be the one that opened it), never
   force-push, never bypass a red test suite.
