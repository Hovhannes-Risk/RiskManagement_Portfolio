# Project B — ML Anomaly Detection

Two complementary detectors that produce **surveillance signals — not automatic account actions**. Outputs feed into Project A (dashboard) and Project C (PDF reports).

## Why two detectors

A single statistical test fires often and produces noise. The design here is intentionally conservative: a player is only flagged when **independent methods agree**. This raises the bar for action and keeps the false-positive rate manageable for a single-operator desk.

## 1. Same-second bot detector — `bot_detection.py`

**Operational definition:** an account placing ≥2 bets within the same one-second window.

Manual placement requires reading the market, selecting an outcome, entering a stake, and confirming — typically 2–4 seconds end-to-end. Sub-second placements at scale are inconsistent with human behaviour.

**Result on the dataset:** 457 accounts flagged.

## 2. Statistical / ML ensemble — `ml_anomaly.py`

Three independent flags combined into an `Anomaly_Score` (0–3):

| Method | Triggers when |
|--------|---------------|
| Z-score | > 3 on any of: bet count, stake, avg stake, win rate, avg odds |
| IQR outlier | Outside 1.5×IQR on ≥2 of the same features |
| Isolation Forest | Anomaly flag at `contamination = 0.1` |

**Score → risk band:**

| Score | Band |
|-------|------|
| 3 | CRITICAL |
| 2 | HIGH |
| 1 | MEDIUM |
| 0 | NORMAL |

Action threshold = agreement across all three. Single-method hits go to a review queue, not to action.

## Outputs

| File | Contents |
|------|----------|
| `master_analysis.xlsx` | 6-sheet consolidated workbook (Summary, Sport, Market, League, Client_KPIs, ML_Anomaly) |
| `winning_low_volume_players.xlsx` | The $255k sharp-account cohort (≤20 bets, net house loss) |
| `ml_anomaly_detection.xlsx` | Full ensemble output with per-player scores |
| `detailed_analysis.xlsx` | Per-feature breakdowns for case review |

## Files


Project_B_ML_Anomaly_Detection/
├── README.md              This file
├── bot_detection.py       Same-second detector
├── ml_anomaly.py          Z-score + IQR + Isolation Forest ensemble
└── sample_output/         Anonymized results (xlsx)


## Run locally

bash
pip install -r ../requirements.txt
python bot_detection.py
python ml_anomaly.py


Both scripts read anonymized sample data and write to `sample_output/`. Original raw wallet identifiers and the de-anonymization map are not part of this repository.

## Known limitations

- **No CLV data.** Without closing-line value, the sharp-player flag relies on win rate and stake-velocity proxies. Adding CLV would tighten the signal materially.
- **Single-period view.** All features are computed over the full dataset; rolling-window versions would catch behaviour change earlier.
- **No labelled ground truth.** The detectors are unsupervised — precision/recall cannot be reported. Validation is by operational review, not test set.

## Cross-references

- Outputs consumed by `Project_A_Dashboard/risk_dashboard.py`
- Methodology details in `Documentation/methodology.md` §3 (same-second), §4 (multi-account)
- Anonymization rule in `Documentation/methodology.md` §7

## Stack

Python 3.10+ · pandas · numpy · scikit-learn · scipy · openpyxl
