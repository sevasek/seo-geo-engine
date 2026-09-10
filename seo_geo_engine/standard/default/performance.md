# Performance — default rules

## Performance

| ID | Rule | Source | Weight | Status | Unblock requirement |
|---|---|---|---|---|---|
| PERF-001 | Raw HTML payload is under 250KB per page. | Core Web Vitals / performance fundamentals | 1 | open | — |
| PERF-002 | Largest Contentful Paint (LCP) meets Google's "Good" threshold (<=2.5s). | Core Web Vitals | 3 | open | — |
| PERF-003 | Cumulative Layout Shift (CLS) meets Google's "Good" threshold (<=0.1). | Core Web Vitals | 3 | open | — |
| PERF-004 | Interaction to Next Paint (INP) meets Google's "Good" threshold. | Core Web Vitals | 3 | blocked | Needs real-user field/CrUX data — no lab-data substitute exists for INP, and a lower-traffic site may not accumulate enough CrUX data for Google to report it at all. |
