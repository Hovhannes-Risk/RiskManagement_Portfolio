# Senior Review Notes — Weekly Risk Report

**Reviewer:** Hovhannes Asatryan (Risk Manager, 15 years industry experience)
**Report under review:** `ai_output/ai_weekly_risk_report.md`
**Review date:** 21 May 2026
**Time spent:** 35 minutes

---

## Purpose of this document

The AI report is the *first draft*. This document is the *second draft* — the human-judgment layer that hiring managers want to see and that production-grade AI deployment requires.

For each recommendation in the AI report I have applied one of four verdicts:

- **ACCEPT** — the AI got this right; ship as-is.
- **MODIFY** — the AI got the direction right, but the magnitude / scope / timing is wrong.
- **REJECT** — the AI's recommendation is operationally unsafe or analytically unsupported.
- **DEFER** — the recommendation is reasonable but the second-signal confirmation has not happened yet.

Production rule: **no AI-recommended action enters the operations queue without a verdict line in this file.**

---

## Verdict summary

| Action # | AI recommendation | Verdict | Net change |
|---|---|---|---|
| 1 | Manual settlement audit of 325 Champions League winners | **MODIFY** | Narrow the audit, tighten the operational definition |
| 2 | Velocity cooldown + manual review for 20 same-second accounts | **MODIFY** | One-size cooldown is wrong; tier by stake density |
| 3 | Tiered margin review on Football FTR | **DEFER** | One period is not enough; flag for next-period review |
| 4 | Margin review on CS2 IEM markets | **REJECT** | Single-period CS2 variance is high; sample insufficient |
| 5 | Passive monitoring of 174 low-volume winners | **ACCEPT** | This is the right posture |
| 6 | Investigation routing for behavioural clusters | **ACCEPT (with caveat)** | Route, but cap investigator hours |

**Net effect of my overrides:** the AI report's Action Table contains 6 items totalling an estimated 60+ investigator-hours and a Football margin change touching ~$80k of weekly stake. After my review, 2 actions enter the queue, 1 is deferred to next period, 1 is rejected, and 2 are accepted with scope adjustments. Estimated investigator-hours after my overrides: 18. Margin changes: 0 this period.

The point is not that the AI was wrong. The point is that **a senior risk manager's first job is to be the brake**, especially on one period of observation.

---

## Action 1 — Champions League settlement audit

**AI recommendation:** Manual audit of all 325 winning Champions League tickets. Cross-check settlement timestamps against event end. Review pre-match suspension windows around team-news releases.

**Verdict: MODIFY.**

The AI is right that the CL anomaly is the single most important finding in this report. The statistics are sound: 469 settled bets with a Wilson 95% lower bound at 65% is well above the 55% operational threshold and is the largest single concentration of unexplained house loss.

But "audit all 325 winners" is the kind of recommendation that gets written by someone who has never had to staff an audit. Three things wrong with it as written:

1. **325 tickets at ~6 minutes per ticket is 32 audit-hours.** That's nearly a person-week. Before committing that, the cheaper check is to look at *which* matches drove the win rate — if 80% of the wins concentrated in a handful of fixtures, those are the fixtures to audit first.

2. **"Pre-match suspension windows around team-news releases"** is vague. Operational definition: I want a 60-minute window before kick-off cross-referenced with team-sheet release timestamps. If wins concentrate in that window, that's the insider-information hypothesis confirmed.

3. **The audit needs a STOP condition.** The AI doesn't define one. If the first 50 tickets show no settlement issues and no team-news concentration, the audit ends and the finding is parked. Without a stop condition, audits run until someone tires of them, which is worse than not auditing.

**Modified action:**

> Audit Champions League winning tickets in tranches of 50, ordered by:
> 1. Tickets settled > 30 minutes after event end (probe settlement-timing hypothesis first — cheapest to fix if true).
> 2. Tickets placed in the 60-minute pre-kick-off window (probe insider-info hypothesis second).
> 3. All remaining winning tickets only if tranches 1–2 surface a pattern.
>
> STOP condition: if the first 50 audited tickets show no settlement-timing issues AND no team-news concentration, end the audit and re-evaluate at next period. Document findings either way.

**Cost saved by the modification:** ~24 audit-hours if tranches 1–2 come back clean. The headline action remains; the operational scope tightens.

---

## Action 2 — Same-second bot velocity cooldown

**AI recommendation:** Apply velocity-based cooldown (≤1 placement per second per account per market). Force CAPTCHA / re-authentication on accounts breaching the threshold > 5 times per day. Manual review of placement history for the 20 flagged accounts.

**Verdict: MODIFY.**

The AI is right that 20 same-second-placement accounts is a strong scripted-activity signal. It's also right that the velocity-cooldown approach is the standard mitigation. Two problems with the specifics:

1. **A one-size velocity cooldown punishes the wrong people.** Three of the 20 flagged accounts (P15, P3, P18) are also in the top-winners table with > 100 bets each. These are either skilled rapid placers or sophisticated scripters — applying a 1-bet-per-second hard cap to a recreational scripter who places £1 bets is fine; applying it to a £100-stake account that wins £600 a week is a £4k/month volume hit on three accounts. Need a stake-tier:
   - Tier A (avg stake < $20): hard cap 1 bet/sec, no exception.
   - Tier B (avg stake $20–$100): soft cap, allow 2 bets/sec, log and alert on 3+.
   - Tier C (avg stake > $100): no automated cap, route to manual review (these are the accounts that pay the bills if they're legitimate; you do not want to lose them to a false positive).

2. **The CAPTCHA threshold "> 5 times per day" is arbitrary.** Empirically, a legitimate user occasionally bursts 2-bet placements when correcting a slip error. The right threshold from my operational experience is 10+ breaches in a 60-minute rolling window, not 5/day. The AI's threshold would CAPTCHA 60% of legitimate users at least once per month, which destroys session conversion.

3. **The manual review of P15, P3, P18 is needed FIRST** — before any automated control is applied. If they turn out to be skilled rapid placers (one of them keeps a Pinnacle-style market-monitoring spreadsheet open, places by hotkey), the cooldown applied to them is a customer-loss event. If they're scripted, the cooldown is the right answer.

**Modified action:**

> 1. Manual review of P15, P3, P18 within 48 hours — review their placement history, market preferences, and timing patterns. Confirm scripted vs skilled-manual.
> 2. Apply tiered velocity controls only after the manual review:
>    - Tier A accounts (avg stake < $20): hard cap 1 bet/sec.
>    - Tier B accounts (avg stake $20–$100): soft cap, alert on 3+/sec.
>    - Tier C accounts (avg stake > $100): no automated cap; manual-review tier.
> 3. CAPTCHA trigger: 10+ same-second placements in any 60-minute rolling window (NOT 5/day).

**Cost saved by the modification:** potential customer-loss event on three accounts avoided pending review. If even one of those accounts is a skilled-but-legitimate player, the modification has paid for itself.

---

## Action 3 — Football FTR margin review

**AI recommendation:** Tiered margin review on Football FTR markets (tier-1 leagues +0.5%, tier-2 +1.0%).

**Verdict: DEFER.**

The AI got the structure right — margin tiering is the correct lever, not account restriction — but acted on a single-period observation. Football FTR is the highest-volume, deepest-liquidity, most-modelled market in the industry. A $1.9k loss across $25k of weekly stake (−7.7% hold) sits inside one-sigma weekly variance for that book size in my experience. One observation is not enough to move margins. Two consecutive periods at this hold rate, or one period below −10%, is.

**The margin change is the right action. The decision is too early.**

**Modified action:**

> Re-evaluate Football FTR margins at end of next reporting period:
> - If hold is again below −5% on $20k+ weekly stake → execute the tiered increase as the AI proposed.
> - If hold reverts to the −3 to +3% band → no change; close the finding.
> - If hold deteriorates further (below −10%) → escalate; the margin change is not the right response, the pricing model is.

**Note in the watchlist; do not action this period.**

---

## Action 4 — CS2 IEM margin review

**AI recommendation:** Margin review on CS2 IEM markets (−$2,050 P&L on $9.1k stake).

**Verdict: REJECT.**

This is the AI being mechanical. CS2 is a notoriously high-variance market segment because:

- Match-up coverage by traders is thinner than football.
- Player-form factors (one player having a bad night) drive outcomes more than they do in team sports with broader squads.
- Stake density is lower, so each large winning ticket has outsized P&L impact.

A −22% hold on 382 settled bets is, in CS2 specifically, well inside expected variance. I have seen single tournaments produce −40% hold on similar sample sizes that fully reverted the next event. Recommending a margin change on this observation is the kind of action that destroys volume in a segment that needs volume to be profitable.

**Action: REJECT this recommendation; do not change CS2 margins on this observation.**

Instead: tag CS2 hold as a watchlist item with a 3-period observation window. If 3 consecutive periods show hold below −15% on > 300 bets, escalate to the CS2 trader for a model review (not an across-the-board margin call).

---

## Action 5 — Passive monitoring of 174 low-volume winners

**AI recommendation:** Passive monitoring of 174 low-volume winning accounts; re-evaluate at 50 bets.

**Verdict: ACCEPT.**

This is correct. 174 accounts with ≤20 bets each cannot be classified without more data; restriction is the wrong action; monitoring is the right action. The 50-bet re-evaluation threshold matches the methodology.

One small implementation note: the system should *automatically* re-surface any account from this cohort that crosses 50 bets, rather than waiting for the next periodic review. Operationally that's a database query; it doesn't need a human in the loop.

---

## Action 6 — Behavioural cluster investigation routing

**AI recommendation:** Route the Layer-2 behavioural cluster set to investigations for KYC overlap checks.

**Verdict: ACCEPT, with caveat.**

The recommendation is correct: behavioural-only signals should not produce account actions but should produce investigation tickets. The caveat is a cost-cap: behavioural clustering at scale produces many candidate clusters, most of which dissolve under KYC review.

**Operational addition:**

> Investigation effort cap on Layer-2 clusters: maximum 1 investigator-hour per cluster. If KYC overlap is not surfaced within that time, the cluster is parked. This prevents the investigation team from being absorbed by speculative pattern-matches.

This isn't a disagreement with the AI; it's the operational guardrail the AI didn't think to write.

---

## What the AI got right that surprised me

Three places the AI's output was better than the average junior analyst's would be:

1. **It surfaced its own confidence downgrades.** Section 8 of the report explicitly says "the report is NOT acting on these three findings, and here is why." That's the discipline gate doing its job — without it, the AI would have action-listed the 174 low-volume winners. Junior analysts often skip this because admitting what you can't do feels like a weakness; in fact it is the credibility anchor.

2. **It separated trader-side actions from account-side actions.** The AI correctly identified that Football FTR is a trader-side lever (margin) and not an account-side lever (restriction). Junior analysts conflate these two routinely.

3. **It refused to list Layer-2 cluster member IDs in the report.** The compliance instinct was correct: surface the count, not the names, until investigation completes.

These three patterns are senior-analyst behaviour. The prompts encoded them; the model executed them.

---

## What the AI got wrong that the validation layer must catch

Three places the AI was structurally weak — the kind of weakness that doesn't go away with better prompting:

1. **No sense of operational cost.** The AI happily recommends 32+ audit-hours and margin changes touching $80k of stake on one period of observation. The model has no model of staffing, customer attrition, or volume sensitivity. The validation layer has to supply that.

2. **One-size threshold defaults.** "CAPTCHA threshold: 5 breaches per day" is the kind of number an LLM picks because it sounds reasonable. In production, those numbers come from A/B testing and customer-conversion impact analysis. Until they do, every threshold needs a human override.

3. **No regime awareness.** CS2 variance behaves differently from Football variance; the AI applied a single mental model. Senior judgment is sport-specific, market-specific, and seasonal. This will never come from the model alone.

These three weaknesses are why the validation layer is not optional. They are why hiring a senior risk manager remains worth doing even after the AI report is automated.

---

## Final operational summary

After my overrides:

- **2 actions enter the queue this period:** the modified Champions League audit (tranche-based, with stop condition) and the modified bot velocity cooldown (manual review of P15/P3/P18 first, then tiered enforcement).
- **1 action is deferred to next period:** Football FTR margin review.
- **1 action is rejected:** CS2 IEM margin change.
- **2 actions are accepted with implementation guardrails:** passive monitoring of low-volume cohort (auto-re-surface at 50 bets), behavioural cluster routing (1-hour investigation cap).

The system as a whole is functioning correctly: the AI did the analysis, the discipline gate downgraded the over-claims, and my override layer added operational context. None of these three steps is sufficient alone.

---

*Reviewed and approved by: Hovhannes Asatryan, Risk Manager.*
*Next review: Week of 28 April 2026 data.*
