# CRAWL-002 — robots.txt doesn't fully disallow known AI-answer-engine crawlers.

**Rule:** robots.txt doesn't fully disallow known AI-answer-engine crawlers.

**Evidence the check emits:** The `robotsTxt` body, naming which AI crawler user-agents are Disallow: /.

**Kind of change that flips it:** Stop blanket-blocking GPTBot / ClaudeBot / Google-Extended / etc. unless that is an explicit business decision documented in a profile override.

**Depends on:** `CMS-ACCESS`

Edit robots.txt. A `Disallow: /` for `User-agent: *` also blocks them. If you intend to block AI crawlers, disable this ID in site.yaml with a reason — don't leave it failing.

Apply the change in the site's own repo or CMS. Re-crawl, confirm the
verdict flipped, then run `seo-geo-plan-sync` so the row is deleted.
Do not hand-edit a generated report.
