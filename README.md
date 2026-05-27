# Risk Management Portfolio

**AI-enabled risk analytics for sports betting operations.**
*Hovhannes Asatryan — 15 years industry experience (Live Trader → Live Manager → Risk Manager)*

## 🚀 Live Demo

[**Open Interactive Risk Dashboard →**](https://riskmanagementportfolio-hkdaavgx3tsjvuzyrutvng.streamlit.app/)

Live deployed Streamlit app showing real-time risk monitoring, ML-based bot detection, and multi-account similarity alerts on 4,138 anonymized betting transactions.

![Dashboard Overview](Project_A_Dashboard/screenshots/dashboard_overview.png)

---

## 🎥 Video Demo

[▶️ Watch 2‑minute dashboard walkthrough on Loom](https://www.loom.com/share/c772edb48a4d4679939865a8c653eadf)

Quick tour of real‑time risk monitoring, bot detection, and PDF reporting.

## TL;DR

Four production-style projects analysing a **526,232-bet dataset** across **12,208 wallets** and **19 sports**.
End-to-end: data cleaning → anomaly detection → interactive dashboard → automated PDF reporting → **AI-enabled weekly analysis with human-judgment override layer**.

**Headline findings, all quantified from real data:**

| # | Finding | Impact |
|---|---|---|
| 1 | 457 accounts placing ≥2 bets in the same one-second window | Scripted activity / bot population |
| 2 | $255,000 in unrecovered house losses concentrated in players with ≤20 bets | Classic sharp-player signature |
| 3 | 75.5% player win rate in Champions League markets | Inconsistent with random variance — insider / settlement audit needed |
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

— produced per-sport averages aligned with real market prices (Football 2.50, Tennis 2.67, Basketball 2.63, CS2 3.02, Table Tennis 2.98). Every downstream metric that depends on odds — risk scoring, sharp detection, market-quality monitoring — was then rebuilt on the correct field.

Full derivation: [`Documentation/methodology.md`](Documentation/methodology.md) §2.

This is the kind of issue that silently biases every dashboard built on top of it. Surfacing it required reading the data, not the spec.

---

## Portfolio structure

```
RiskManagement_Portfolio/
│
├── Documentation/
│   ├── methodology.md           Technical methodology (anonymization, detection, scoring)
│   ├── findings_summary.md      Six risk signals, ordered by impact
│   └── data_dictionary.md       Every field, raw and derived
│
├── Project_A_Dashboard/         Streamlit multi-page risk dashboard
│   ├── risk_dashboard.py        326 lines — KPI tracking, player drill-down, PDF export
│   ├── screenshots/             UI captures (PDF)
│   └── sample_output/           Anonymized exports (.xlsx)
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

└── Project_D_AI_Risk_Analysis/  AI-enabled weekly risk workflow
    ├── analytical_pipeline/     Python pre-processor → analytical_brief.json
    ├── prompts/                 7-step methodology with input/output contracts
    ├── ai_output/               LLM-generated weekly risk report
    └── human_validation/        Senior-judgment override layer (the differentiator)
```

---

## Project A — Interactive Risk Dashboard

**Stack:** Streamlit · pandas · plotly · fpdf2

Multi-page dashboard for the risk desk. Loads the anonymized analysis files produced by Project B and exposes:

- **KPI strip** — bets, players, stake, GGR, hold %
- **Bot suspects panel** — accounts with ≥2 placements in the same one-second window
- **Player drill-down** — risk band, win rate, sport mix, CLV proxy
- **Multi-account pairs view** — composite similarity ≥90 flagged CRITICAL
- **PDF export** — one-click summary for the trading team

Run locally:

```bash
cd Project_A_Dashboard
streamlit run risk_dashboard.py
```

Screenshots: [`Project_A_Dashboard/screenshots/`](Project_A_Dashboard/screenshots/)

---

## Project B — ML Anomaly Detection

**Stack:** pandas · scikit-learn · scipy

Two complementary detectors, both designed to produce *surveillance signals* — not automatic account actions.

**1. Same-second bot detector** (`bot_detection.py`)
Operational definition: an account placing ≥2 bets within the same one-second window. Manual placement requires reading the market, selecting an outcome, entering a stake, and confirming — typically 2-4 seconds end-to-end. **457 accounts** flagged in the dataset.

**2. Statistical / ML ensemble** (`ml_anomaly.py`)
Three independent flags combined into an `Anomaly_Score` (0-3):

- **Z-score** > 3 on any of bet count, stake, avg stake, win rate, avg odds
- **IQR outlier** on ≥2 of the same features
- **Isolation Forest** anomaly flag (contamination = 0.1)

Score → band: 3 = CRITICAL, 2 = HIGH, 1 = MEDIUM, 0 = NORMAL.

The ensemble is intentionally conservative — a single statistical test fires often; agreement across three independent methods is the action threshold.

Outputs in [`Project_B_ML_Anomaly_Detection/sample_output/`](Project_B_ML_Anomaly_Detection/sample_output/):
- `master_analysis.xlsx` — 6-sheet consolidated workbook (Summary, Sport, Market, League, Client_KPIs, ML_Anomaly)
- `winning_low_volume_players.xlsx` — the $255k sharp-account cohort
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

1. `analytical_pipeline/run_analysis.py` reads the anonymized sample data, computes KPIs, Wilson 95% confidence intervals, sample-size flags, bot-detection signals, and behavioural clusters. The LLM does **no arithmetic** anywhere in this workflow.
2. A 7-step prompt chain (selected from the 15-step methodology) synthesises the brief into a weekly risk report. Each prompt has an explicit input contract, output contract, and documented failure modes from V1–V4 iteration.
3. The senior validation layer in `human_validation/` applies a per-action verdict (ACCEPT / MODIFY / REJECT / DEFER) and logs the override rate.

**This period's headline result:** the AI report produced 6 action recommendations. The override layer accepted 2 unchanged, accepted 2 with operational guardrails, deferred 1 to next period, and rejected 1. **Override rate: 50%** — the expected band for one-period AI-driven analysis without CLV data.

**Why this project matters:** most "AI risk analysis" portfolios demonstrate what AI does. This one demonstrates what AI *can't* do, and the override layer is the differentiator. Hiring managers reading [`human_validation/senior_review_notes.md`](Project_D_AI_Risk_Analysis/human_validation/senior_review_notes.md) see operational cost awareness, regime-specific judgment, and explicit refusal of single-period action calls — instincts a model alone does not have.

Full report: [`Project_D_AI_Risk_Analysis/ai_output/ai_weekly_risk_report.md`](Project_D_AI_Risk_Analysis/ai_output/ai_weekly_risk_report.md)
Override layer: [`Project_D_AI_Risk_Analysis/human_validation/`](Project_D_AI_Risk_Analysis/human_validation/)

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

**AI risk analysis pipeline:**
```bash
python Project_D_AI_Risk_Analysis/analytical_pipeline/run_analysis.py
```
This regenerates `analytical_brief.json` — the single source of truth that the 7-step prompt chain consumes. The prompts themselves are reproduced verbatim in `Project_D_AI_Risk_Analysis/prompts/`; running them through any current frontier LLM produces the weekly report.

All scripts read from anonymized sample data shipped in each `sample_data/` directory. Original raw wallet addresses and the de-anonymization map are kept private.

---

## Data and confidentiality

- All wallet identifiers anonymized to `P1…P12208` via a sorted, deterministic mapping.
- The `bettor_mapping_PRIVATE.xlsx` is kept outside the repository.
- Anonymization happens **once** upstream — every output downstream is consistent across projects.
- See [`Documentation/methodology.md`](Documentation/methodology.md) §7 for the full anonymization rule.

---

## Tech stack

| Layer | Tools |
|---|---|
| Data | pandas · openpyxl |
| ML / stats | scikit-learn · scipy · numpy |
| Visualisation | plotly · matplotlib |
| Dashboard | Streamlit |
| Reporting | matplotlib (PdfPages) · fpdf2 |
| Language | Python 3.10+ |

---

## About

15 years in the sports-betting industry — live trader (2011–2017), live manager on the basketball desk (2017–2024), now risk manager (2025–). This portfolio is the technical companion to operational experience: the methodology document is what a senior risk manager actually thinks about; the code is what makes that thinking reproducible.

Open to roles in **AI-enabled risk management**, **trading risk**, and **sportsbook quant analytics**.

---

## License

Code: MIT. Findings, methodology text, and report layouts: portfolio use only, no redistribution without attribution.
