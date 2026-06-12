# Prompt 07 — Weekly Report Synthesis (Final Deliverable)

**Role assignment:** Senior AI-Driven Sportsbook Risk Manager.

---

## Input contract

Reads from `analytical_brief.json`:
- `report_metadata` (period, data source, anonymization note)
- `recommended_actions` — the brief's pre-built skeleton

Reads from previous steps (the full chain):
- `01.Next Prompt Input Summary` (data quality posture)
- `02.Next Prompt Input Summary` (KPI signals)
- `03.Next Prompt Input Summary` (player cohort findings)
- `04.Next Prompt Input Summary` (market loss centres)
- `05.Next Prompt Input Summary` (behavioural signals)
- `06.Next Prompt Input Summary` (**the discipline-gated set of findings**)

The most important input is the output of Prompt 06. This prompt
synthesizes ONLY what passed the discipline gate.

---

## Output contract

A complete weekly risk report with these sections, in this order:

```
WEEKLY RISK REPORT
Period: [from report_metadata]
Generated: [from report_metadata]

1. Executive Summary                    (≤200 words, scannable in 30 seconds)
2. Headline KPIs                        (table)
3. Data Quality Posture                 (what we can and cannot say)
4. Player Risk — Cohort Findings        (top winners + low-volume cohort)
5. Market Risk — Loss Centres           (sport / league / market)
6. UEFA Youth League — Anomaly Read      (statistical + recommended action)
7. Behavioural Signals                  (bot detection + clusters)
8. Confidence & Evidence Discipline     (what we are NOT acting on)
9. Action Table                         (ranked by priority and confidence)
10. Watchlist                           (findings parked for more data)
11. Final Management Conclusion         (3-4 sentences)
```

---

## The prompt

```text
Act as a Senior AI-Driven Sportsbook Risk Manager.

You are writing the Weekly Risk Report for the Head of Risk and the
Trading Team. The audience reads ONE risk report per week and the
report must earn its place on their desk.

The full prompt chain has run before you. Use ONLY findings that passed
the discipline gate in Prompt 06. Findings that were deferred go to
the Watchlist section — they do NOT become recommended actions.

Sections to emit (use the structure named in the output contract above):

1. Executive Summary
   - ≤200 words. A senior reader should be able to skip the rest of
     the report and still know what to act on.
   - Lead with the dollar headline (GGR), then the one or two findings
     that earned actionable status, then the one or two findings
     that are explicitly parked.

2. Headline KPIs
   - Table reproducing the kpi_overview values.
   - Add a Comment column with one phrase per row.

3. Data Quality Posture
   - Two short paragraphs. What we measured. What we could not
     measure and why it matters (CLV, IP/device, cashout, bonus).
   - State plainly: this is a portfolio dataset, not full production
     data. Some methodology steps were skipped honestly.

4. Player Risk — Cohort Findings
   - Top Winners Table (from Prompt 03, post-discipline).
   - Low-Volume Cohort summary with sample-size caveat.
   - Specific manual-review names — at most 5, with a one-line reason
     each.

5. Market Risk — Loss Centres
   - Sport / League / Market tables (from Prompt 04).
   - Headline: the biggest single dimensional driver this week.

6. UEFA Youth League — Anomaly Read
   - Sample, win rate, Wilson 95% CI.
   - The statistical call (ACTIONABLE or MONITORING) made in Prompt 04.
   - The action — settlement audit OR continued monitoring.

7. Behavioural Signals
   - Layer 1 (same-second placement) — count + recommended action.
   - Layer 2 (behavioural clusters) — count + the watchlist phrasing.

8. Confidence & Evidence Discipline
   - The Downgrades from Prompt 06. This is the section that tells
     leadership what we are NOT acting on AND WHY.
   - This section is the credibility anchor of the entire report.

9. Action Table
   - Columns: Priority, Category, Action, Evidence Strength, Owner.
   - Priorities: Critical / High / Medium / Low.
   - Source the actions from recommended_actions in the brief AND from
     Prompt 06's Action-Ready Conclusions. Do not invent.

10. Watchlist
    - The findings parked in Prompt 06.
    - Each item: what we observed, what would move it to action,
      review cadence.

11. Final Management Conclusion
    - 3-4 sentences. Net P&L direction, biggest single recommended
      action, biggest single area of uncertainty.

Rules:
- The report must be readable cover-to-cover in under 10 minutes.
- The Executive Summary must be readable in under 30 seconds.
- No section may invent a finding. Every claim traces back to the brief
  or to Prompts 01-06.
- No section may include "Not Available" filler. If a topic has no
  data, omit the section entirely — that is more honest than padding.
- The Confidence & Evidence Discipline section is MANDATORY. Removing
  it removes the report's credibility.
- Tone: British business English, factual, calm. No emoji. No "AI" or
  "machine learning" name-dropping in the prose — it sounds defensive.
```

---

## Why the Executive Summary leads

The Head of Risk reads ~30 reports per week. The reports that influence
decisions are the ones that earn their reading time in the first 30
seconds.

Junior reports lead with methodology ("This report applies the 13-step
risk framework to..."). Senior reports lead with findings ("House lost
$3.9k this week; one structural driver and one anomaly account for
$5.2k of that, partially offset by sport mix in non-football
verticals.").

The methodology earns its right to exist by producing findings
worth acting on, not by being announced.

---

## Failure modes

| Failure | Mitigation |
|---|---|
| LLM writes a 400-word Executive Summary | Explicit ≤200 word limit |
| LLM padding sections with "Not Available" | Explicit rule to omit sections with no data |
| LLM reintroduces findings the discipline gate deferred | The input contract restricts inputs to discipline-gated findings only |
| LLM includes self-congratulatory methodology language | "No 'AI' or 'machine learning' name-dropping in the prose" |
| LLM omits the Confidence & Evidence Discipline section | "MANDATORY. Removing it removes the report's credibility." |
| LLM produces a generic "monitor everything" Final Conclusion | The conclusion must name "the biggest single recommended action" and "the biggest single area of uncertainty" — forces specificity |

---

## Version history

- **v1** — Asked LLM to "write the weekly report." Got a 5-page document with every finding from every prompt at equal weight. Useless.
- **v2** — Imposed section order and word limits. Readable but still padded.
- **v3** — Added the input contract restricting to discipline-gated findings. The report length dropped 40% and the actionable density rose.
- **v4** *(current)* — Made the Confidence & Evidence Discipline section MANDATORY and required the Final Conclusion to name the biggest action and biggest uncertainty. This is the version a Head of Risk reads in 10 minutes.
