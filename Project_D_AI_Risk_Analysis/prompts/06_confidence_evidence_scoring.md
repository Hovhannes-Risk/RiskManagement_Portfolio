# Prompt 06 — Confidence & Evidence Scoring

**Role assignment:** Senior Risk Decision Quality Analyst.

---

## Why this prompt exists

This is the prompt that prevents the report from acting like every other AI risk
report on the internet. Without this step, the LLM's natural tone is
**confident** — it will recommend action on weak signals because the
preceding prompts have asked for action recommendations.

This prompt's job is to **downgrade** confidence claims that the
sample size or evidence quality does not support, and to **upgrade**
findings that have multiple independent confirmations.

If this prompt did nothing else, it would still earn its place: it is
the discipline gate before any operational action enters the final
report.

---

## Input contract

Reads from `analytical_brief.json`:
- `confidence_and_evidence` — pre-computed evidence rollup.

Reads from previous steps:
- `02.Next Prompt Input Summary` (KPI signals)
- `03.Next Prompt Input Summary` (player cohorts + cohort-level Risk/Confidence)
- `04.Next Prompt Input Summary` (market loss centres + per-dimension Risk/Confidence)
- `05.Next Prompt Input Summary` (behavioural signals + per-layer Risk/Confidence)

---

## Output contract

1. Evidence Discipline Headline
2. Findings Confidence Table (every finding from prompts 02–05)
3. Confidence Downgrades (where to back off)
4. Confidence Upgrades (where multiple signals confirm)
5. False-Positive Risk Notes
6. Action-Ready Conclusions (the green-lit subset for Prompt 07)
7. Defer-to-More-Data Conclusions (the parking lot)
8. Next Prompt Input Summary

---

## The prompt

```text
Act as a Senior Risk Decision Quality Analyst.

You are the LAST CHECK before recommendations enter the final report.
Every finding from prompts 02-05 arrives here with a Risk Level and a
Confidence Level. Your job is to AUDIT those, not to invent new ones.

You may DOWNGRADE confidence. You may UPGRADE confidence where two or
more independent signals point the same way. You may NOT introduce a
finding that was not present in the prior chain.

Use the brief's confidence_and_evidence section as your scoring rubric
and starting point — but do not treat it as final. Your task is to
re-grade with the chain context in mind.

Sections to emit (in order, with these exact names):

1. Evidence Discipline Headline
   - One paragraph: the role of this step. State plainly that the
     downstream report will act ONLY on findings that pass this gate.

2. Findings Confidence Table
   - Columns: Finding, Source Prompt, Original Confidence, Re-graded
     Confidence, Evidence Strength, Notes.
   - Every finding from prompts 02-05 must appear.
   - "Re-graded Confidence" is your call.

3. Confidence Downgrades
   - For each finding you downgraded, ONE bullet with the reason.
   - Most common reasons:
     * Sample size below methodology threshold
     * Single-signal claim (e.g. profit without CLV confirmation)
     * Statistical inference treated as direct evidence
   - This section is operationally important — it tells leadership
     what NOT to act on.

4. Confidence Upgrades
   - For each finding you upgraded, ONE bullet with the cross-signal
     that justified the upgrade.
   - Example: "Bot suspect cohort overlaps with UEFA Youth League
     winners by 40% → behavioural + market signals confirm each other."
   - If no upgrades are warranted, state that explicitly. Empty
     section beats invented one.

5. False-Positive Risk Notes
   - 3-5 bullets naming the SPECIFIC false-positive risks this week's
     report carries.
   - Examples: "P124 looks sharp but n=8 — likely variance",
                "UEFA Youth League win rate could revert next week".

6. Action-Ready Conclusions
   - The findings with High or Very High re-graded confidence.
   - These are the ONLY findings that Prompt 07 (Action Management)
     may translate into operational action.

7. Defer-to-More-Data Conclusions
   - The findings with Low or Medium re-graded confidence.
   - These go to a watchlist, not an action list.

8. Next Prompt Input Summary
   - 3-4 sentences telling the Action Management prompt exactly which
     findings it may act on, which go to monitoring, and which are
     parked.

Rules:
- A high Risk Score with low confidence does NOT trigger heavy limits.
  This is the methodology's most-violated rule when LLMs are run
  without this gate.
- A medium Risk Score with multi-signal confirmation MAY trigger
  manual review (not restriction).
- Behavioural fingerprint matches alone are Medium evidence; combined
  with shared market loss concentration, they become Strong.
- If you upgrade, name the second signal. If you downgrade, name the
  weakness. No upgrade or downgrade without a stated reason.
- Tone: explicit, conservative, evidence-graded. The senior signal is
  the willingness to say "we cannot act on this yet."
```

---

## Why this is the senior differentiator

A junior portfolio shows AI generating a risk report.
A senior portfolio shows AI generating a risk report **and a
discipline layer that catches its own over-claims**.

The implicit message to a hiring manager:

> "I know that LLMs produce confident-sounding output by default. I
> built the system to mistrust itself. The discipline gate is mine,
> not the model's."

This is the same instinct a senior risk manager has when a trader
brings a "great" P&L: figure out the variance, the sample size, and
the regime risk before celebrating.

---

## Failure modes

| Failure | Mitigation |
|---|---|
| LLM keeps every Confidence Level from prior prompts unchanged (no actual auditing) | Output contract requires the Re-graded column AND the Downgrades section AND the Upgrades section to be populated |
| LLM invents new findings here | Explicit rule: "You may NOT introduce a finding that was not present in the prior chain" |
| LLM upgrades without naming the second signal | Explicit rule: "If you upgrade, name the second signal" |
| LLM produces empty Downgrades section | Empirically, every weekly run has at least 2 valid downgrades. If the LLM produces none, the prompt is failing — re-run with a stricter system message. |

---

## Version history

- **v1** — Asked LLM to "review the confidence levels." LLM rubber-stamped everything.
- **v2** — Added explicit Downgrades / Upgrades sections. LLM started downgrading.
- **v3** — Added the requirement to name a second signal for any upgrade. Caught a class of fake upgrades.
- **v4** *(current)* — Added Action-Ready vs Defer-to-More-Data partitioning. Downstream prompt now has explicit input contract instead of having to re-read the whole confidence table.
