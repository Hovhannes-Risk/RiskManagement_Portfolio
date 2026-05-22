# Prompt Failure Modes — What Went Wrong During Development

*Production-grade prompt engineering is iterative. This document captures the failure modes encountered while building the 7-step methodology, the patches applied, and the rationale. Hiring managers reading this should understand: the prompts in this repository are V3/V4, not V1.*

---

## Why this document exists

A portfolio that shows only the final prompts is misleading. The prompts that work are the ones that survived rounds of failure. The interesting work is the iteration, not the final text.

---

## Failure mode catalogue

### F-01: LLM hallucinates KPI values

**Prompt affected:** 02 (KPI Synthesis), v1.

**Observed behaviour:** Given the raw bet table inline in the prompt, the LLM was asked to compute hold %. Across 10 test runs, 1 returned a value off by 0.3 percentage points — small enough to escape casual review, large enough to drive a wrong action recommendation downstream.

**Root cause:** LLMs do not do reliable arithmetic on long lists of decimals. Their failure is silent; the output looks confident.

**Fix:** Moved all arithmetic to Python (`analytical_pipeline/run_analysis.py`). The LLM now receives a pre-computed brief and is forbidden from recomputing any value. Determinism restored.

**Senior signal:** This is the single most important insight in this repository. Treat the LLM as a *synthesizer*, never as a *calculator*.

---

### F-02: LLM labels every winner as "Sharp"

**Prompt affected:** 03 (Player Risk Scoring), v1.

**Observed behaviour:** Given a list of profitable players, the LLM defaulted to labelling all of them as "Sharp" or "High Risk", regardless of bet count. A player with 4 bets and 100% win rate was rated CRITICAL.

**Root cause:** The prompt asked the LLM to classify players and didn't constrain it on sample size. The model pattern-matched on "profitable" → "sharp".

**Fix:** Added a binding rule with a numerical threshold: "Do not classify a player as Sharp/Professional based on win rate or ROI alone when sample size is below ~50 bets." Combined with pre-aggregation into two cohorts (top-winners and low-volume), the false-positive rate dropped to near zero.

**Senior signal:** LLMs respond well to *numerical* thresholds and badly to *qualitative* instructions like "be conservative."

---

### F-03: LLM rubber-stamps confidence levels

**Prompt affected:** 06 (Confidence & Evidence), v1.

**Observed behaviour:** Asked to "review the confidence levels from prior prompts," the LLM returned the same confidence levels with minor wording changes. The discipline gate did nothing.

**Root cause:** The prompt asked for a review without forcing the model to *change anything*. LLMs default to agreement.

**Fix (v2):** Added explicit `Downgrades` and `Upgrades` sections to the output contract. The LLM had to populate both. Empty sections were flagged as a prompt failure.

**Fix (v3):** Required the LLM to name a *second signal* for any upgrade. Without this, the model invented justifications for upgrades that weren't supported.

**Fix (v4, current):** Partitioned the output into `Action-Ready Conclusions` vs `Defer-to-More-Data Conclusions`. This forces the model to actually classify each finding rather than producing a homogeneous review.

**Senior signal:** Asking the model to *audit itself* without structural constraints produces theatre, not auditing.

---

### F-04: LLM recommends account closures from one week of data

**Prompt affected:** 03 (Player Risk Scoring), v1.

**Observed behaviour:** Given a high-ROI low-volume player, the LLM recommended "account closure" or "permanent restriction" as action.

**Root cause:** The prompt did not state which actions were operationally appropriate at which evidence level. The model picked the action that sounded most decisive.

**Fix:** Added explicit binding rule: "Do NOT recommend account closures or hard limits based on this week's data alone." Combined with the methodology's tiered framework (Low → Monitor; Medium → Manual Review; High → Limit; Critical → Escalate), the model now matches action to evidence.

**Senior signal:** LLMs do not know the operational cost of an action. Every action recommendation needs an explicit ceiling on severity tied to evidence strength.

---

### F-05: LLM treats Champions League like any other loss centre

**Prompt affected:** 04 (Market Risk), v1.

**Observed behaviour:** Asked to analyse market-level losses, the LLM ranked Champions League third on the list and recommended a margin increase, identical to its recommendation for Football FTR and CS2.

**Root cause:** Margin increases are the default trader-side response to negative hold. The LLM applied this universally without considering whether the *cause* of the loss was pricing weakness or something structural.

**Fix:** Created a dedicated `Champions League Anomaly Read` section with an explicit statistical test (Wilson CI lower bound vs 55% threshold). When the test passes, the action is integrity-side (settlement audit) not trader-side (margin). When the test fails, monitoring only.

**Senior signal:** Different mechanisms produce different losses. A flat "review margins" output is junior; an output that diagnoses *why* the loss happened and routes to the correct lever is senior.

---

### F-06: LLM lists Layer-2 cluster member IDs in the final report

**Prompt affected:** 05 (Behavioural Fingerprinting), v1.

**Observed behaviour:** Asked to surface behavioural cluster matches, the LLM included member IDs in the final report — names that, without case-level investigation, should not be surfaced.

**Root cause:** The brief contained the IDs; the prompt didn't say "do not list them in the report."

**Fix:** Explicit rule in v2: "Do NOT list specific cluster members." Added compliance rationale to the prompt body so the LLM understands *why* the rule exists and doesn't try to creatively comply.

**Senior signal:** Surface counts in narrative reports; route IDs through controlled investigative workflows. This is a compliance / data-protection instinct LLMs do not have natively.

---

### F-07: LLM writes a 400-word Executive Summary

**Prompt affected:** 07 (Weekly Report Synthesis), v1.

**Observed behaviour:** The Executive Summary was expansive, repeated content from later sections, and could not be read in 30 seconds.

**Root cause:** No length constraint and no clear definition of *what* the summary should privilege.

**Fix (v2):** Hard cap at 200 words.

**Fix (v3):** Plus an explicit lead structure: "Lead with the dollar headline, then the one or two findings that earned actionable status, then the one or two findings that are explicitly parked."

**Senior signal:** Executive summaries that are not skimmable are not read. A Head of Risk reads ~30 reports per week; the summary either earns the rest of the report's reading time in 30 seconds or it doesn't.

---

### F-08: LLM omits the Confidence & Evidence section in the final report

**Prompt affected:** 07 (Weekly Report Synthesis), v2.

**Observed behaviour:** The LLM treated the Confidence & Evidence Discipline section as optional, and dropped it when the report ran long.

**Root cause:** The prompt didn't tell the model the section was the report's credibility anchor.

**Fix:** Made it MANDATORY in the prompt body, with the rationale: "Removing it removes the report's credibility."

**Senior signal:** The section that says "we are NOT acting on these things and here is why" is more important than the action list. Hiring managers read this section first.

---

## What didn't work

A few approaches I tried that didn't pan out and were reverted:

- **System message asking the LLM to "be skeptical."** Produced nervous, hedged output without actually downgrading anything. Reverted.
- **Chain-of-thought prompts asking the LLM to "think step by step."** Made outputs longer without improving accuracy. Removed.
- **Few-shot examples of "good" risk reports.** The LLM pattern-matched on the example structure and lost the dataset-specific findings. Removed; replaced with explicit output contracts.

**Senior signal:** Generic prompting techniques (CoT, few-shot, role-play) often help less than specific constraints (numerical thresholds, output contracts, binding rules).

---

## Version pinning

The prompts in this repository are versioned in their respective files (`v1`, `v2`, etc. in the `Version history` section of each prompt). When the underlying LLM is updated, regressions are possible — the prompts should be re-validated against a held-out set of weekly briefs before deployment.

**Validation harness:** not yet built. This is a known gap. In production, the next deliverable after this portfolio piece would be a small evaluation suite that:

1. Runs the 7 prompts against 4 weeks of held-out briefs.
2. Captures the override log for each week.
3. Tracks the override rate over time.
4. Alerts when the override rate moves out of the 30–60% expected band — either direction indicates the prompts need attention.

That harness is the production-readiness step beyond this portfolio.
