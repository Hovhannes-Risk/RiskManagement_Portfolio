# Action Override Log

*Quick-reference audit trail of what entered operations vs what the AI recommended. One row per AI recommendation. Stored separately from the narrative review for compliance and management dashboards.*

| Period | AI Action # | Category | AI recommended | Verdict | Net change | Saved cost | Notes |
|---|---|---|---|---|---|---|---|
| 2026-05 | 1 | Integrity | Audit all 344 YL winning tickets | **MODIFY** | Tranche-based, stop-condition added | ~25 audit-hrs if tranches 1–2 clean | Operational scope tightened; finding unchanged |
| 2026-05 | 2 | Bot mitigation | Velocity cooldown + 5/day CAPTCHA threshold | **MODIFY** | Tiered by stake density; manual review of P01646/P01845/P09542 first | Potential customer-loss event on 3 high-value accounts avoided | CAPTCHA threshold corrected from 5/day → 10/60min rolling |
| 2026-05 | 3 | Market margin | Football FTR margin +0.5%/+1.0% | **DEFER** | Re-evaluate next period | $80k weekly stake protected from premature change | One-period observation insufficient |
| 2026-05 | 4 | Market margin | CS2 IEM margin review | **REJECT** | No margin change | CS2 volume preserved | Inside CS2-specific variance band |
| 2026-05 | 5 | Watchlist | Passive monitoring of 174 low-vol winners | **ACCEPT** | Auto-re-surface at 50 bets added | — | Implementation note appended |
| 2026-05 | 6 | Investigation | Cluster routing to investigations | **ACCEPT (caveat)** | 1-hour investigation cap per cluster | Investigation team protected from absorbing speculative load | Cost-cap added |

---

## Verdict definitions

- **ACCEPT** — AI recommendation enters operations queue unchanged.
- **MODIFY** — AI recommendation enters operations queue with operational adjustments (scope, threshold, sequencing).
- **REJECT** — AI recommendation does not enter operations queue. Reasoning logged.
- **DEFER** — AI recommendation parked on watchlist; re-evaluated next period.

---

## Period summary statistics

| Metric | This period |
|---|---|
| AI recommendations made | 6 |
| Accepted unchanged | 1 |
| Accepted with caveat | 1 |
| Modified | 2 |
| Deferred | 1 |
| Rejected | 1 |
| AI accuracy rate (Accept / Accept+caveat) | 33% |
| AI directional accuracy rate (Accept + Modify) | 67% |
| Override rate | 50% (3 of 6) |

*Override rate is expected to remain in the 30–60% range for AI-generated risk reports operating without CLV data and against weekly observation windows. A trending-down override rate over multiple periods would indicate the prompts are improving; a trending-up rate would indicate the model is drifting and the prompts need revision.*

---

## Sign-off

| Role | Name | Date |
|---|---|---|
| Risk Manager (reviewer) | Hovhannes Asatryan | 2026-05-21 |
| Head of Risk (approver) | *Pending* | — |
| Compliance (informed) | *Pending* | — |
