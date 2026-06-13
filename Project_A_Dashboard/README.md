# Project A — Interactive Risk Dashboard

## 🚀 Live Demo

[**Open Interactive Risk Dashboard →**](https://riskmanagementportfolio-hkdaavgx3tsjvuzyrutvng.streamlit.app/)

Live deployed Streamlit app showing real-time risk monitoring, ML-based bot detection, and multi-account similarity alerts on a 4,319-bet synthetic trading day.
*Streamlit multi-page dashboard. Surveillance layer for the risk desk:
KPIs at a glance, drill-down to player level, one-click PDF export.*

## Screenshots
<img width="1904" height="624" alt="01_overview" src="https://github.com/user-attachments/assets/b0b48bdb-2917-45e6-85e9-24dc683a07aa" />



<img width="1904" height="632" alt="02_risk_charts" src="https://github.com/user-attachments/assets/13bb2bdd-030f-440c-bf45-5ab83cb15707" />



<img width="1908" height="726" alt="03_player_risk" src="https://github.com/user-attachments/assets/f9d6492d-468e-4678-9d06-1b8553965454" />


---

## Why a dashboard

The PDF reports in Project C are a scheduled deliverable — they run on a
fixed cadence and answer the question *"what happened?"* The dashboard
answers a different question: *"what's happening right now, and which
player should I look at first?"*

Three things it does that the PDFs do not:

1. **Live filtering** — narrow the entire view to a date range or
   risk band without regenerating a report.
2. **Player drill-down** — search any account ID, see their full
   risk profile in one panel.
3. **Operator-side export** — one-click CSV of the filtered slice,
   ready for compliance routing.

---

## What it surfaces

The Overview page is the homepage of the risk desk.

| Section                | Signal                                                          |
| ---------------------- | --------------------------------------------------------------- |
| KPI strip              | Bets, players, stake, GGR, hold %, bot suspects                 |
| Bot suspects metric    | Distinct accounts placing ≥2 bets in the same one-second window |
| GGR daily trend        | Loss/gain trajectory with hover-level detail                    |
| Alert banners          | CRITICAL risk level players · negative GGR · multi-account hits |
| Top Risk Players table | Top 10 by composite risk score (loaded from Project B output)   |
| GGR by Sport bar       | Diverging colour scale — red for loss, green for win            |

The Player Risk page is the drill-down. Filter by risk band (CRITICAL
→ MINIMAL), search a specific account ID, export the filtered
result as CSV with one button.

The Multi-Account page surfaces the Project B similarity output —
pairs of accounts above the 90-composite-score threshold flagged as
CRITICAL. The recommended workflow before action is documented in
[`Documentation/methodology.md`](../Documentation/methodology.md) §4
(KYC pull → device fingerprint → compliance escalation).

The Analytics page is the exploratory tail — distributions of odds and
stake, hourly betting pattern, sport-level bubble chart. No alerts
fire from this page; it exists for trader-side intuition building.

---

## Data provenance

All data shipped in `sample_data/` is **fully synthetic** — a one-day
slice of the deterministic dataset produced by
`data_generator/generate_sportsbook_data.py` (seed 42). No real player
exists behind any `P{N}` identifier. Generation happens once upstream;
every downstream surface stays consistent.

## Stack and rationale

| Layer        | Choice                                                                                                                                            |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Framework    | **Streamlit** — minimal scaffolding for a single-operator tool. Tableau is the alternative, but adds licensing and limits the export logic.       |
| Charts       | **plotly** — interactive hover, no static-image fallback needed for desktop use.                                                                  |
| PDF export   | **fpdf2** — single-file PDF generation without LaTeX or headless browser dependencies.                                                            |
| Data loading | `pd.read_excel` with `@st.cache_data` — Streamlit's caching layer keeps re-runs cheap when the user only changes a filter.                        |
| Layout       | Tabs as a sidebar radio (`📊 Overview`, `🔍 Player Risk`, `⚠️ Multi-Account Alerts`, `📈 Analytics`) — each page is single-purpose, no scroll fatigue. |

---

## Files

```
Project_A_Dashboard/
├── README.md                  This file
├── risk_dashboard.py          Single-file Streamlit app
├── sample_data/               Synthetic inputs (generator outputs)
│   ├── mydata_sample.xlsx
│   ├── player_risk_scores.xlsx
│   └── multi_account_detection.xlsx
├── screenshots/               UI captures (PNG, embedded below)
└── sample_output/             Example CSV exports
```

---

## Run locally

```bash
pip install -r ../requirements.txt
streamlit run risk_dashboard.py
```

The app opens at `http://localhost:8501`. All four pages load from the
files in `sample_data/`. If the optional risk-score or multi-account
files are absent the corresponding pages show a graceful warning
rather than crashing.

---

## Known limitations

- **Single-user tool.** The cache layer assumes one operator at a
  time; the dashboard is not designed for shared deployment in its
  current form. A production deployment would replace `@st.cache_data`
  with a session-scoped cache.
- **Read-only.** No write-back path — flags and notes stay in the
  operator's CSV export. A production version would integrate with
  the case-management system.
- **Sample data only.** The committed `sample_data/` is a synthetic one-day slice;
  and intentionally limited in scope. Full-volume runs (526k bets)
  require pointing the loader at the production extract.

---

## Cross-references

- Risk scores consumed here are produced by
  [`Project_B_ML_Anomaly_Detection/`](../Project_B_ML_Anomaly_Detection/)
- Same-second bot signal logic is documented in
  [`Documentation/methodology.md`](../Documentation/methodology.md) §3
- Multi-account similarity logic in
  [`Documentation/methodology.md`](../Documentation/methodology.md) §4
- The PDF reports the dashboard's export button generates use the
  same template family as
  [`Project_C_Automated_Reports/`](../Project_C_Automated_Reports/)
