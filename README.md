# Risk Management Portfolio

[![CI](https://github.com/Hovhannes-Risk/RiskManagement_Portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/Hovhannes-Risk/RiskManagement_Portfolio/actions/workflows/ci.yml)

**AI-enabled risk analytics for sports betting operations.**
*Hovhannes Asatryan — 15 years industry experience (Live Trader → Live Manager → Risk Manager)*

## 🚀 Live Demo
https://riskmanagementportfolio-hkdaavgx3tsjvuzyrutvng.streamlit.app/

<img width="1904" height="624" alt="01_overview" src="https://github.com/user-attachments/assets/f71f5d32-346b-4dbf-9561-b26a5e32f0fc" />
<img width="1904" height="632" alt="02_risk_charts" src="https://github.com/user-attachments/assets/8b2706fa-724e-4822-8cc6-cbc7d41cd7a3" />
<img width="1908" height="726" alt="03_player_risk" src="https://github.com/user-attachments/assets/30128411-3d22-4969-bb54-bfd8db40b215" />



---

## 🎥 Video Demo

[▶️ Watch 2‑minute dashboard walkthrough on Loom](https://www.loom.com/share/c772edb48a4d4679939865a8c653eadf)

Quick tour of real‑time risk monitoring, bot detection, and PDF reporting.

## TL;DR

Five production-style projects analysing a **fully synthetic 526,232-bet dataset** across **12,208 accounts** and **19 sports** — generated deterministically (seed 42) by a committed generator that plants realistic risk patterns sized from 15 years of live-book experience. Synthetic ground truth means detector quality is **provable, not claimed**: CI verifies recall of the planted bots, sharps, and coordinated pairs on every push. No real player data exists anywhere in this repository or its history.
End-to-end: data cleaning → anomaly detection → interactive dashboard → automated PDF reporting → **AI-enabled weekly analysis with human-judgment override layer** → AML/RG compliance rules engine.
Shared analytical primitives live in the unit-tested `risk_core/` package; **21 pytest checks run in CI on every push** (badge above).

**Headline findings — every one reproducible from the seeded generator:**

| # | Finding | Impact |
|---|---|---|
| 1 | 464 accounts placing ≥2 bets in the same one-second window (460 planted + 4 coincidental) | Scripted activity / bot population |
| 2 | $517k of house losses concentrated in the top 100 low-volume winners (≤20 bets) | Classic sharp-player signature |
| 3 | 77.5% player win rate in UEFA Youth League (344/444, Wilson CI 73.4-81.1%) | Thin-league insider pattern — survives Bonferroni correction |
| 4 | $82,600 in net house losses on the "Full Time Result" market | Trader-side line-management lever |

Detailed prioritisation in [`Documentation/findings_summary.md`](Documentation/findings_summary.md).

---

## The work behind the numbers

### The `resolved_odds` discovery

Initial KPI generation produced an average-odds column with values **below 1.0** — a representative row read `Avg_Odds = 0.71`. Decimal odds cannot be below 1.0 by definition, so the number was the trigger to investigate rather than the answer to report.

Inspection of raw rows showed `resolved_odds` was the **net return multiplier**, not the decimal odds: `decimal_odds − 1` on a win, `0.00` on a loss. All 237,602 lost bets in the dataset carried zero, dragging the naive average toward zero across every player.

The corrected formula —

```
Avg_Won_Odds = mean(resolved_odds + 1) over won bets only
```

— produces correct per-sport averages near real market prices. The dataset deliberately reproduces this field-semantics trap from my production career: `resolved_odds` stores the net multiplier, and every consumer that assumes "odds" silently breaks. The corrected formula is unit-tested.

Full derivation: [`Documentation/methodology.md`](Documentation/methodology.md) §2.

This is the kind of issue that silently biases every dashboard built on top of it. Surfacing it required reading the data, not the spec.

---

## Portfolio structure

```
RiskManagement_Portfolio/
│
├── data_generator/              Seeded synthetic dataset generator (the data's single source of truth)
│   └── generate_sportsbook_data.py
│
├── Documentation/
│   ├── methodology.md           Technical methodology (provenance, detection, scoring)
│   ├── findings_summary.md      Six risk signals, ordered by impact
│   └── data_dictionary.md       Every field, raw and derived
│
├── Project_A_Dashboard/         Streamlit multi-page risk dashboard
│   ├── risk_dashboard.py        Single-file app — KPI tracking, player drill-down, PDF export
│   ├── sample_data/             Shared synthetic sample day (used by all projects)
│   ├── screenshots/             UI captures (PNG, embedded in READMEs)
│   └── sample_output/           Generated exports (.xlsx)
│
├── Project_B_ML_Anomaly_Detection/
│   ├── ml_anomaly.py            Isolation Forest + Z-score + IQR ensemble
│   ├── bot_detection.py         Low-volume sharp-player detector
│   └── sample_output/           6 Excel files (master_analysis.xlsx is the consolidated workbook)
│
└── Project_C_Automated_Reports/
    ├── daily_report.py          Daily Risk Report (matplotlib + PdfPages)
    ├── weekly_report.py         Weekly Executive Summary
    └── sample_output/           Example PDFs

├── Project_D_AI_Risk_Analysis/  AI-enabled weekly risk workflow
│   ├── analytical_pipeline/     Python pre-processor → analytical_brief.json
│   ├── prompts/                 7-step methodology with input/output contracts
│   ├── ai_output/               LLM-generated weekly risk report
│   └── human_validation/        Senior-judgment override layer (the differentiator)
│
├── Project_E_Regulated_Compliance/  MGA/UKGC AML + RG rules engine (synthetic data)
│   ├── generate_synthetic_data.py   Seeded generator with planted patterns
│   └── compliance_engine.py         Typed rules → escalation queue
│
├── risk_core/                   Shared, typed, unit-tested analytical primitives
└── tests/                       21 pytest checks (run by CI on every push)
```

---

## Project A — Interactive Risk Dashboard

**Stack:** Streamlit · pandas · plotly · fpdf2

Multi-page dashboard for the risk desk. Loads the generated analysis files and exposes:

- **KPI strip** — bets, players, stake, GGR, hold %
- **Bot suspects panel** — accounts with ≥2 placements in the same one-second window
- **Player drill-down** — risk band, win rate, sport mix, CLV proxy
- **Multi-account pairs view** — composite similarity ≥90 flagged CRITICAL
- **PDF export** — one-click summary for the trading team

Run commands for every project are consolidated in [How to run](#how-to-run) below. Screenshots are embedded in [`Project_A_Dashboard/README.md`](Project_A_Dashboard/README.md).

---

## Project B — ML Anomaly Detection

**Stack:** pandas · scikit-learn · scipy

Two complementary detectors, both designed to produce *surveillance signals* — not automatic account actions.

**1. Same-second bot detector** (`bot_detection.py`)
Operational definition: an account placing ≥2 bets within the same one-second window. Manual placement requires reading the market, selecting an outcome, entering a stake, and confirming — typically 2-4 seconds end-to-end. **464 accounts** flagged in the dataset — against 460 planted, with the 4 extras being exactly the coincidental false-positive class documented in methodology §10.

**2. Statistical / ML ensemble** (`ml_anomaly.py`)
Three complementary flags combined into an `Anomaly_Score` (0-3):

- **Z-score** > 3 on any of bet count, stake, avg stake, win rate, avg odds
- **IQR outlier** on ≥2 of the same features
- **Isolation Forest** anomaly flag (contamination = 0.1)

Score → band: 3 = CRITICAL, 2 = HIGH, 1 = MEDIUM, 0 = NORMAL.

The ensemble is intentionally conservative — a single statistical test fires often; agreement across the methods is the action threshold. The detectors share a feature set, so agreement is a precision filter rather than independent confirmation — see methodology.md §5.

Outputs in [`Project_B_ML_Anomaly_Detection/sample_output/`](Project_B_ML_Anomaly_Detection/sample_output/):
- `master_analysis.xlsx` — 6-sheet consolidated workbook (Summary, Sport, Market, League, Client_KPIs, ML_Anomaly)
- `winning_low_volume_players.xlsx` — the low-volume sharp cohort ($517k in its top 100)
- `ml_anomaly_detection.xlsx`, `detailed_analysis.xlsx`

---

## Project C — Automated PDF Reporting

**Stack:** matplotlib · PdfPages · pandas

Two reports, both designed to be schedulable via Windows Task Scheduler (no daemon, no infrastructure).

| Report | Cadence | Audience | Sections |
|---|---|---|---|
| Daily Risk Report | Daily | Risk desk | KPIs · top risks · bot suspects · sport breakdown |
| Weekly Executive Summary | Weekly | Management | Trends · loss analysis · recommendations |

Layout uses manual `fig.add_axes([x, y, w, h])` placement (0–1 figure-relative coordinates) rather than the grid system — keeps cards, headers, and tables on a deterministic pixel grid so week-over-week diffs are meaningful.

Sample output: [`Project_C_Automated_Reports/sample_output/`](Project_C_Automated_Reports/sample_output/)

---

## Project D — AI-Enabled Risk Analysis with Human Override

**Stack:** pandas · numpy · scipy (Wilson CI) · LLM (model-agnostic prompt chain) · Markdown

A weekly risk-analysis workflow that uses an LLM as a synthesis tool inside a discipline-gated pipeline, with a documented human-judgment override layer. The thesis: **AI does the analysis, humans hold the gating function.**

**Pipeline:**

1. `analytical_pipeline/run_analysis.py` reads the generated data, computes KPIs, Wilson 95% confidence intervals, sample-size flags, bot-detection signals, and behavioural clusters. The LLM does **no arithmetic** anywhere in this workflow.
2. A 7-step prompt chain (selected from the 15-step methodology) synthesises the brief into a weekly risk report. Each prompt has an explicit input contract, output contract, and documented failure modes from V1–V4 iteration.
3. The senior validation layer in `human_validation/` applies a per-action verdict (ACCEPT / MODIFY / REJECT / DEFER) and logs the override rate.

**This period's headline result:** the AI report produced 6 action recommendations. The override layer accepted 2 unchanged, accepted 2 with operational guardrails, deferred 1 to next period, and rejected 1. **Override rate: 50%** — the expected band for one-period AI-driven analysis without CLV data.

**Why this project matters:** most "AI risk analysis" portfolios demonstrate what AI does. This one demonstrates what AI *can't* do, and the override layer is the differentiator. Hiring managers reading [`human_validation/senior_review_notes.md`](Project_D_AI_Risk_Analysis/human_validation/senior_review_notes.md) see operational cost awareness, regime-specific judgment, and explicit refusal of single-period action calls — instincts a model alone does not have.

Full report: [`Project_D_AI_Risk_Analysis/ai_output/ai_weekly_risk_report.md`](Project_D_AI_Risk_Analysis/ai_output/ai_weekly_risk_report.md)
Override layer: [`Project_D_AI_Risk_Analysis/human_validation/`](Project_D_AI_Risk_Analysis/human_validation/)

---

## Project E — Regulated-Market Compliance Layer (Synthetic)

**Stack:** pandas · numpy · dataclasses · pytest

Projects A–D analyse the synthetic sportsbook dataset; Project E extends
the same philosophy to **MGA/UKGC-style AML and responsible-gambling
monitoring.**
A seeded synthetic generator plants four behaviour classes (deposit
structuring under the EDD threshold, loss-chasing redeposits, night-session
escalation, withdrawal reversals) plus a clean baseline; a typed rules engine
recovers them into an escalation queue with severity, evidence, recommended
action, and the regulatory obligation each alert maps to.

Because the patterns are planted, the engine's quality is **provable, not
claimed**: CI asserts ≥80% recall per pattern and ≤5% false positives on
clean players on every push. The engine never acts on a player — every alert
routes to a human queue, the same gating thesis as Project D.

Details: [`Project_E_Regulated_Compliance/README.md`](Project_E_Regulated_Compliance/README.md)

---

## Testing and CI

`tests/` contains 21 pytest checks covering the portfolio's core invariants:
Avg_Won_Odds can never fall below 1.0; the Wilson CI stays inside [0,100] and
the published Champions League bound reproduces; the bot detector flags a
synthetic scripted account while clearing humans and batch slips; the shipped
s sample passes schema and synthetic-ID gates; the compliance engine meets its
recall/precision bars. GitHub Actions runs the suite plus a smoke-run of every
entry point on Python 3.11 and 3.12 for each push (badge at the top).

---

## How to run

```bash
git clone <repo-url>
cd RiskManagement_Portfolio
pip install -r requirements.txt
```

**Dashboard:**
```bash
streamlit run Project_A_Dashboard/risk_dashboard.py
```

**Anomaly detection batch:**
```bash
python Project_B_ML_Anomaly_Detection/ml_anomaly.py
python Project_B_ML_Anomaly_Detection/bot_detection.py
```

**PDF reports:**
```bash
python Project_C_Automated_Reports/daily_report.py
python Project_C_Automated_Reports/weekly_report.py
```

**Compliance engine (synthetic):**
```bash
python Project_E_Regulated_Compliance/compliance_engine.py
```

**Tests:**
```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

**AI risk analysis pipeline:**
```bash
python Project_D_AI_Risk_Analysis/analytical_pipeline/run_analysis.py
```
This writes a fresh `analytical_brief_regenerated.json` from the public sample. The committed `analytical_brief.json` — the brief behind the published weekly report — was generated from a 30-day production window and is preserved as-is, so the published numbers stay verifiable. The prompts themselves are reproduced verbatim in `Project_D_AI_Risk_Analysis/prompts/`; running them through any current frontier LLM produces the weekly report.

All scripts read from a single shared synthetic sample — `Project_A_Dashboard/sample_data/mydata_sample.xlsx` (one trading day, 4,319 bets, 3,160 accounts) — so every project runs out-of-the-box after `pip install -r requirements.txt`. The **full 526,232-bet dataset regenerates deterministically** with `python data_generator/generate_sportsbook_data.py` (gitignored parquet; same seed, same bytes, same findings). Generated results land in each project's gitignored `outputs/` folder; the committed `sample_output/` folders hold results from the full dataset.

---

## Data provenance — fully synthetic by design

- Every row is generated by [`data_generator/generate_sportsbook_data.py`](data_generator/generate_sportsbook_data.py) with a fixed seed. **No real player, account, or transaction exists anywhere in this repository or its history.**
- Why synthetic: real operational data cannot be published in any form, and "anonymized" aggregates remain proprietary. Synthetic data resolves the conflict honestly — and buys something real data never can: **provable recall.** The generator plants the bot, sharp, insider-league, and coordinated-pair patterns at known ground truth; CI asserts the detection stack recovers them on every push.
- The patterns themselves are the ones I spent 15 years catching on live books — the generator encodes that operational experience so the detectors have honest work to do.
- See [`Documentation/methodology.md`](Documentation/methodology.md) §1 and §7 for generator design rules.

## Tech stack

| Layer | Tools |
|---|---|
| Data | pandas · openpyxl |
| ML / stats | scikit-learn · scipy · numpy |
| Visualisation | plotly · matplotlib |
| Dashboard | Streamlit |
| Reporting | matplotlib (PdfPages) · fpdf2 |
| Quality | pytest (21 checks) · GitHub Actions CI |
| Language | Python 3.10+ |

---

## About

15 years in the sports-betting industry — live trader (2011–2017), live manager on the basketball desk (2017–2024), now risk manager (2025–). This portfolio is the technical companion to operational experience: the methodology document is what a senior risk manager actually thinks about; the code is what makes that thinking reproducible.

Open to roles in **AI-enabled risk management**, **trading risk**, and **sportsbook quant analytics**.

---

## License

Code: MIT. Findings, methodology text, and report layouts: portfolio use only, no redistribution without attribution.
