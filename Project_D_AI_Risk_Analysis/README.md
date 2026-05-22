# Project D — AI-Enabled Risk Analysis

**A weekly sportsbook risk analysis workflow that uses an LLM as a synthesis tool inside a discipline-gated pipeline, with a documented human-override layer.**

---

## The thesis

Most "AI risk analysis" portfolios show what AI **does**: a methodology, some prompts, an output report. That's a junior portfolio.

This one shows what AI **can't do**, and how the system is structured to compensate. The senior signal is not the model — it is the discipline gate, the override log, and the human judgment that catches the model's predictable failure modes before they enter operations.

15 years in the sports-betting industry has taught me one thing about every risk system, AI-driven or not: **the value lives in the override rate, not the accept rate.**

---

## Architecture

```
┌──────────────────────┐
│ sample_data/         │   anonymized betting data (10k bets, 499 wallets)
│ mydata_sample.xlsx   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────┐
│ analytical_pipeline/run_analysis.py                       │
│                                                            │
│ - Python computes all KPIs, confidence intervals,         │
│   sample-size flags, bot-detection signals,               │
│   behavioural clusters                                     │
│ - LLM does NO arithmetic in this entire pipeline           │
│                                                            │
│ → emits analytical_brief.json                              │
└──────────┬───────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────┐
│ prompts/  —  7-step chain                                  │
│                                                            │
│   01 Data Quality Audit                                    │
│   02 KPI Synthesis                                         │
│   03 Player Risk Scoring                                   │
│   04 Market Risk Analysis                                  │
│   05 Behavioural Fingerprinting                            │
│   06 Confidence & Evidence Scoring  ◄── Discipline gate    │
│   07 Weekly Report Synthesis                               │
│                                                            │
│ Each prompt has: input contract, output contract,          │
│ failure modes documented, version history                  │
└──────────┬───────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────┐
│ ai_output/ai_weekly_risk_report.md                         │
│                                                            │
│ AI-generated weekly report — 6 actions, 4 watchlist items │
└──────────┬───────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────┐
│ human_validation/  —  the differentiator                   │
│                                                            │
│   senior_review_notes.md     ← per-action verdicts        │
│   action_override_log.md     ← audit trail               │
│   prompt_failure_modes.md    ← iteration history          │
│                                                            │
│ Override rate this period: 50% (3 of 6 AI actions)         │
└──────────────────────────────────────────────────────────┘
```

---

## The 7 prompts (and why these, not the full 15)

The full 15-step methodology lives in `Documentation/methodology.md`. This production workflow uses **7 of the 15**, selected for what the portfolio dataset actually supports. Padding a report with "Not Available" entries for steps that can't run is a junior signal; honest scoping is a senior signal.

| Selected | Step | Why |
|---|---|---|
| ✅ | 01 — Data Quality Audit | Honest reporting starts here |
| ✅ | 02 — KPI Synthesis | Numerical backbone |
| ✅ | 03 — Player Risk Scoring | Core domain signal |
| ✅ | 04 — Market Risk Analysis | Where loss centres live |
| ✅ | 05 — Behavioural Fingerprinting | Bot detection + cross-account |
| ✅ | 06 — Confidence & Evidence | **The discipline gate** |
| ✅ | 07 — Weekly Report Synthesis | The final deliverable |
| ❌ | 0, 3, 5b, 6, 7, 9, 11 | Either real-time (incompatible with batch) or require fields not captured in this dataset (Pinnacle benchmark, IP, cashout, bonus) |

See `prompts/00_methodology_overview.md` for the full justification.

---

## What this period found

**Period:** 1–30 April 2026 · **10,000 bets** · **499 wallets** · **−$3,871 GGR on $209k turnover**

The pipeline identified six findings. The discipline gate downgraded three of them. The senior validation layer modified two of the remaining three and rejected one. Net: **2 actions entered operations, 1 was deferred, 1 was rejected, 2 were accepted with implementation guardrails**.

The single most important finding was a **Champions League player win rate of 69.3% across 469 settled bets** (Wilson 95% CI lower bound: 65.0%). Statistically above the actionable threshold; operationally narrowed (in my override) to a tranche-based audit with a stop condition rather than a 32-audit-hour open-ended review.

The single biggest **rejection** was the AI's recommendation to change CS2 margins on one period of observation. CS2 variance behaves differently from football variance — the AI applied a single mental model where regime-specific judgment was required. This is the kind of override the senior validation layer exists to make.

Full report: [`ai_output/ai_weekly_risk_report.md`](ai_output/ai_weekly_risk_report.md)
Full override log: [`human_validation/senior_review_notes.md`](human_validation/senior_review_notes.md)

---

## How to read this folder

If you have **5 minutes**, read [`ai_output/ai_weekly_risk_report.md`](ai_output/ai_weekly_risk_report.md) and stop at Section 8 (Confidence & Evidence Discipline). That section is the report's credibility anchor.

If you have **15 minutes**, also read [`human_validation/senior_review_notes.md`](human_validation/senior_review_notes.md). That document is the senior signal — it is what separates this portfolio from a model demo.

If you have **30 minutes** and want to evaluate the engineering, read [`prompts/00_methodology_overview.md`](prompts/00_methodology_overview.md), then the 7 individual prompt files, then [`human_validation/prompt_failure_modes.md`](human_validation/prompt_failure_modes.md). The iteration history (v1 → v4) is where the real work is documented.

---

## How to reproduce

```bash
cd Project_D_AI_Risk_Analysis
python analytical_pipeline/run_analysis.py
```

This regenerates `analytical_brief.json` from the sample data. The brief is the single source of truth for every prompt in the chain. The prompts themselves are reproduced verbatim in this repository — running them through any current frontier LLM with the brief as input should produce a report substantively similar to `ai_output/ai_weekly_risk_report.md` (minor stylistic variation is expected, but the findings should be identical).

---

## What this portfolio is *not*

- **Not a model demo.** The LLM does no arithmetic. The findings come from Python.
- **Not a full production system.** No evaluation harness, no monitoring, no rollback path. These are explicitly listed as next-step work in `prompt_failure_modes.md`.
- **Not a replacement for a risk manager.** The override rate (50% this period) is the explicit demonstration that human judgment remains the gating function.

It is a complete, honest, reproducible demonstration of one human-AI hybrid risk workflow, with the failure modes documented and the override logic explicit.

---

## Stack

| Layer | Tools |
|---|---|
| Data | pandas · openpyxl |
| Stats | numpy · scipy (Wilson CI) |
| LLM | model-agnostic; prompts validated on Claude / GPT class frontier models |
| Reporting | Markdown |
| Discipline | the prompt chain in `prompts/` |
| Judgment | the override layer in `human_validation/` |

---

## License

Methodology and prompts: MIT.
Override log and review notes: portfolio use only, no redistribution without attribution.

---

## Author

Hovhannes Asatryan — 15 years sports-betting industry experience.
Risk Manager (2025–) · Live Manager, basketball desk (2017–2024) · Live Trader (2011–2017).
