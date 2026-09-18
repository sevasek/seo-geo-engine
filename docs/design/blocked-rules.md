# Design: blocked rules and GEO depth

**Status:** proposed (accepted as policy in Phase 2; work that
unblocks a row is Phase 5 unless a profile map is trivial).

**Why this needs a design doc.** Nine default rows are `status:
blocked` with a one-line `@check` stub. They still carry weight, so
they pull every site's score down by a fixed hole. The temptation
is to "implement" them with a heuristic so the score looks more
complete. CLAUDE.md already forbids that when no reliable automated
signal exists. This doc classifies each stub so a future change has
to pick a lane instead of a vibe.

A separate confusion: PERF-002/003 and CRAWL-008 are `open` but
*runtime*-blocked without enrichment. That is not this list. See
[enrichment.md](enrichment.md).

## Decision

There are three kinds of "we don't score this yet." Only one of them
is a default `status: blocked` stub.

### Kind A — no reliable automated signal (engine stub)

A method does not exist that a check could run against crawl data
(or a well-defined extra blob) without pretending.

| ID | Unblock requirement (from the standard) | May grow a real check when… |
|---|---|---|
| CONTENT-005 | Defined keyword-stuffing method beyond naive frequency | A method is published and tested on real pages that humans agree are stuffed vs dense-but-legitimate. Not a `% of words that equal the H1`. |
| CONTENT-006 | Defined skimmability rubric | A rubric with pass/fail examples exists (subheading interval, list presence, paragraph length caps) **and** that rubric is tested on real crawl `bodyText` / heading sequences, not only on made-up fixtures. |
| CONTENT-008 | Distinguish unsupported claims from sourced ones | A claims/sources map or a citation convention that's machine-visible (e.g. consistent footnote markup). Until then, no NLP classifier in this repo. |
| PERF-004 | Real-user field/CrUX INP | Field data is actually present for the site. Even then, this is an enrichment key, not a lab metric. Don't write INP into `pageSpeed` "just in case." |

Kind A stays a stub until that "when" is true. Adding a check that
returns `pass` on empty evidence is worse than a stub.

### Kind B — signal exists, not in the crawl (enrichment)

Not blocked in the standard. Listed here so nobody "fixes" them by
flipping status:

- PERF-002, PERF-003 — PSI lab blob ([enrichment.md](enrichment.md)).
- CRAWL-008 — GSC sitemap blob.

### Kind C — needs a profile-supplied map or policy

The check *could* be written generically if the profile documents a
fact the engine must not guess.

| ID | What the profile would supply | Shape (sketch) |
|---|---|---|
| CONTENT-004 | Per-page (or per-pattern) target intent | `site.yaml` `search_intent:` map of URL glob → `informational` / `commercial` / `navigational`. Check compares page signals (word count, schema type, CTA density — **only once those signals are defined and fixture-tested**) to the declared intent. Until the comparison method exists, the row stays blocked even if a profile fills the map. The map alone is not a check. |
| LINK-006 | Policy for "responsible" external hosts | `external_link_policy:` allow/deny hosts, or "must be cited in playbook X." A check can then classify `a[href]` hosts. Crawler must emit outbound hrefs (it currently keeps *internal* hrefs; this check needs an `externalHrefs` field — that's a crawl-contract MINOR when we do it). |
| LINK-007 | Policy for `rel` on outbound links | Same policy object, with when to require `nofollow` / `sponsored` / `ugc`. Also needs outbound anchors in the crawl. |
| LINK-008 | Set of "new" pages + a surfacing rule | `new_pages:` list or `published_after:` plus a rule like "linked from homepage or hub." A single crawl snapshot cannot know "new" without the profile saying so. |
| CONTENT-007 | Competitor/SERP corpus | A directory of competitor page texts, gathered out of engine. This is the expensive one. Not a Phase 5 default; a profile may try it as an extension ID first. If two profiles succeed with the same method, *then* promote. |

Kind C unblocks in this order:

1. Write the `site.yaml` shape (engine loads it into
   `SiteProfile.to_dict()` so checks can read it).
2. Add crawl fields if missing (`externalHrefs`, etc.) with schema +
   fixtures.
3. Implement the check against fixtures that include the map.
4. Flip the standard row from `blocked` to `open`. Completeness gate
   then demands good/bad fixtures.

Do not skip to 4.

Sample profile's LINK-002 ("anchor text matches target keyword") is
already this pattern: it's a *profile* blocked row because it needs
a page→keyword map. It should not be promoted to an engine default
until a generic map shape exists and at least one real profile uses
it.

## Scoring policy for remaining stubs

Blocked weight in the denominator is **intentional**. It makes the
score read as "of the standard we claim," not "of the subset that's
easy." A profile that finds the hole intolerable has `disabled_ids`
with a reason (e.g. "CONTENT-007 not in scope for this engagement").
That's honest. Zeroing blocked weights in `compute_score` is not —
it would make two sites incomparable.

When a Kind A/C row flips to `open`, that's a MINOR
([versioning.md](versioning.md)). Profiles that disabled it keep the
disable until they drop the ID from `disabled_ids`.

## GEO-specific default rows we already have

The engine is "SEO/GEO" because some *open* rules are about
AI-answer readiness, not because there is a separate GEO scorer:

- CRAWL-002 — don't robots-disallow known AI crawlers.
- CRAWL-006 — content present without JS (extractors and many AI
  fetchers).
- CONTENT-002 — text in real `<p>` (content extractors).
- CONTENT-003 — `dateModified` in JSON-LD.
- SCHEMA-* — machine-readable entities.

That is enough GEO identity for v1. New GEO rows follow the same
engine-vs-profile procedure as SEO rows. "Appeared in a tweet about
citations" is not sufficient to add a blocked stub.

## Alternatives considered

**Drop blocked rows from the default standard until they're
implementable.** Rejected. The rows are a backlog with IDs,
weights, and unblock text. Deleting them is how they get
re-litigated from scratch every quarter. Stubs are cheaper than
amnesia.

**Score two numbers: assessable vs all.** Tempting for dashboards.
Rejected for v1 because two scores will be quoted independently and
drift (CLAUDE.md: two numbers that should agree come from one
function). A later HTML-dashboard toggle that *filters display* to
non-blocked items, while the headline score stays all-in, could be
a Phase 5 UI nicety. It must still call `_points_earned`.

**Let an LLM judge CONTENT-007/008 at report time.** Rejected. The
report pipeline is deterministic and fixture-tested. An LLM judge
cannot live in `@check` without making Layer 1 non-hermetic. A
profile *may* run an offline review and record the result as
enrichment (`site["editorial"]["content007"] = "pass"`) — that's a
Kind C blob, and even then the check is "did the profile record a
pass," which is a process check, not information-gain. Don't add
it as an engine default.

## Implementation notes

- Phase 2: classify CRAWL-008 / PERF-002 as Kind B in the standard
  files' surrounding prose if needed; don't change their status.
- Phase 5: first Kind C candidate that a migrated profile actually
  has a map for (likely LINK-008 or CONTENT-004 if they already
  maintained one in the fork). Port the *shape* to the engine, not
  the values.
- Never add a Kind A stub "so the standard looks complete."
