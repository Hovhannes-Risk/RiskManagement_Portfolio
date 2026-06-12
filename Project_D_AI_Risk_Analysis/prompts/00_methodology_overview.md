# Prompt Methodology — Selected 7-Step Workflow

*This folder contains seven prompts that, run in sequence on the JSON brief
produced by `analytical_pipeline/run_analysis.py`, generate a weekly risk
report. The full 15-step methodology lives in
`Documentation/methodology.md`; this is the production-ready subset.*

---

## Why these seven (and not the others)

The full 15-step methodology was designed for an operator with the
complete data stack: Pinnacle benchmark capture, IP/device fingerprints,
cashout pipeline, bonus flags, real-time alert feeds. The synthetic
portfolio dataset has a narrower field set, so prompts that would emit
`"Not Available"` for every output section have been dropped from this
production workflow rather than padded out with placeholders.

| Step | Selected? | Reason |
|---|---|---|
| 0 — Live Alert Triage | No | Real-time loop, incompatible with batch weekly review |
| 1 — Data Quality | **Yes** | Honest reporting starts here |
| 2 — KPI Calculation | **Yes** | Numerical backbone |
| 3 — Open Bets & Exposure | No | Sample is all settled — no open exposure to analyse |
| 4 — Player Risk Scoring | **Yes** | Core domain signal |
| 5 — Market Risk | **Yes** | Sport/league/market loss centres |
| 5b — Market Context | No | No Pinnacle / Betfair benchmark data captured |
| 6 — CLV Detection | No | Same — no benchmark odds |
| 7 — Cashout Risk | No | Cashout fields not captured |
| 8 — Behavioural Fingerprinting | **Yes** | Bot detection + behavioural clusters |
| 9 — Bet Type Correlation | No | Limited leg-level data in sample |
| 10 — Confidence & Evidence | **Yes** | The senior-level differentiator |
| 11 — Bonus / Promotion | No | No bonus fields captured |
| 12 — Risk Action Management | **Yes** | Operational synthesis |
| 13 — Weekly Report | **Yes** | Final deliverable (numbered `07_` here) |

**Honest scoping is a senior signal.** Padding a report with
`"Not Available"` lines tells a recruiter the methodology was bolted on
to the dataset rather than designed for it.

---

## Execution order

```
analytical_brief.json
        │
        ▼
01_data_quality_audit.md         (audit brief.data_quality)
        │
        ▼
02_kpi_calculation.md            (synthesize brief.kpi_overview)
        │
        ▼
03_player_risk_scoring.md        (interpret brief.player_risk)
        │
        ▼
04_market_risk_analysis.md       (interpret brief.market_risk)
        │
        ▼
05_behavioral_fingerprinting.md  (interpret brief.behavioral_fingerprinting)
        │
        ▼
06_confidence_evidence_scoring.md (override brief.confidence_and_evidence)
        │                          ◄── This is the senior-judgment gate
        ▼
07_weekly_report_synthesis.md    (assemble final report)
        │
        ▼
ai_output/ai_weekly_risk_report.md
```

Each prompt has an explicit:
- **Input contract** — which JSON sections it reads
- **Output contract** — required section names so downstream prompts can chain
- **Failure modes** — patterns I have seen the prompt fail at, and how I guard against them

This is the difference between *prompts* and *prompt engineering*. Prompts
are text. Prompt engineering is the contract around the text, the
versioning, and the documented failure modes.

---

## Standard rules (apply to every prompt)

1. Do not guess missing data. Write "Not Available" where appropriate.
2. Separate confirmed findings from unavailable metrics.
3. Separate settled bets from open bets.
4. Separate company-side P&L from player-side P&L.
5. Add a Confidence Level to every conclusion: Low / Medium / High / Very High.
6. Recommend Actions only when evidence strength supports them.
7. Output sections must use consistent names so downstream prompts can chain.
8. **The LLM is forbidden from doing arithmetic.** All numbers come from
   the analytical brief; the LLM's job is synthesis and narrative.

---

## Standard output schema

Every prompt emits these sections in this order:

```
1. Confirmed Findings
2. Unavailable Metrics
3. Risk Signals
4. Risk Level                  (Low / Medium / High / Critical)
5. Confidence Level            (Low / Medium / High / Very High)
6. Recommended Actions         (or "Insufficient evidence" — explicitly)
7. Next Prompt Input Summary   (carry-forward for the next step)
```

Downstream prompts read `Next Prompt Input Summary` from the previous
step's output. This keeps the chain coherent without re-injecting the
full brief at every step.
