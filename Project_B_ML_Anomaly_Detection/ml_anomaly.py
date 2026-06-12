"""
Statistical / ML anomaly ensemble.

Three flags combined into a 0-3 Anomaly_Score:
  1. |Z| > 3 on any feature (computed on LOG-transformed volume features —
     stake and bet counts are heavily right-skewed, and z-scores on the raw
     scale over-flag the long tail; see methodology.md §5).
  2. IQR outlier on >= 2 features.
  3. Isolation Forest flag (contamination=0.10 — calibrated to the share
     of accounts the desk can realistically triage per cycle, NOT an
     estimate of true anomaly prevalence; documented in methodology.md §5).

The three detectors share the same feature set, so they are correlated —
agreement across them is a precision filter, not three independent
confirmations. The action threshold is score >= 2 for review, 3 for
priority review. Banding logic lives in the unit-tested `risk_core`.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from sklearn.ensemble import IsolationForest

SCRIPT_DIR = Path(__file__).parent
PORTFOLIO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PORTFOLIO_ROOT))

from risk_core import anomaly_level, player_stats  # noqa: E402

DATA_PATH = PORTFOLIO_ROOT / "Project_A_Dashboard" / "sample_data" / "mydata_sample.xlsx"
OUT_DIR = SCRIPT_DIR / "outputs"

FEATURES = ["Total_Bets", "Total_Stake", "Avg_Stake", "Win_Rate", "Avg_Odds_Single"]
LOG_FEATURES = {"Total_Bets", "Total_Stake", "Avg_Stake"}  # right-skewed volume features
IF_CONTAMINATION = 0.10
IF_RANDOM_STATE = 42

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("ml_anomaly")


def load_bets(path: Path = DATA_PATH) -> pd.DataFrame:
    bets = pd.read_excel(path, sheet_name="Raw_Data")
    if "bet_type" not in bets.columns:
        bets["bet_type"] = "Ordinar"
    logger.info("loaded %d bets from %s", len(bets), path.name)
    return bets


def build_features(bets: pd.DataFrame) -> pd.DataFrame:
    """Player-level feature frame for the ensemble."""
    feats = player_stats(bets)
    singles = bets[bets["bet_type"] == "Ordinar"]
    odds = (
        singles.groupby("bettor")
        .agg(Avg_Odds_Single=("odds", "mean"))
        .reset_index()
    )
    feats = feats.merge(odds, on="bettor", how="left")
    feats["Avg_Odds_Single"] = feats["Avg_Odds_Single"].fillna(0.0)
    return feats


def score_ensemble(feats: pd.DataFrame) -> pd.DataFrame:
    """Apply the three detectors and combine into Anomaly_Score / Anomaly_Level."""
    out = feats.copy()

    # 1 — Z-score, log1p on skewed volume features
    for f in FEATURES:
        col = np.log1p(out[f]) if f in LOG_FEATURES else out[f]
        out[f"zscore_{f}"] = np.abs(scipy_stats.zscore(col, nan_policy="omit"))
    out["Max_ZScore"] = out[[f"zscore_{f}" for f in FEATURES]].max(axis=1)

    # 2 — IQR flags
    def iqr_outlier(series: pd.Series) -> pd.Series:
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        return (series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)

    out["IQR_Flags"] = sum(iqr_outlier(out[f]).astype(int) for f in FEATURES)

    # 3 — Isolation Forest
    X = out[FEATURES].fillna(0.0)
    forest = IsolationForest(contamination=IF_CONTAMINATION, random_state=IF_RANDOM_STATE)
    out["IF_Anomaly"] = forest.fit_predict(X) == -1

    out["Anomaly_Score"] = (
        (out["Max_ZScore"] > 3).astype(int)
        + (out["IQR_Flags"] >= 2).astype(int)
        + out["IF_Anomaly"].astype(int)
    )
    out["Anomaly_Level"] = out["Anomaly_Score"].apply(anomaly_level)
    return out


def main() -> None:
    bets = load_bets()
    feats = build_features(bets)
    logger.info("scoring %d players", len(feats))
    scored = score_ensemble(feats)

    print(scored["Anomaly_Level"].value_counts())

    cols = [
        "bettor", "Total_Bets", "Total_Stake", "Avg_Stake", "Win_Rate",
        "Avg_Odds_Single", "Max_ZScore", "IQR_Flags", "IF_Anomaly",
        "Anomaly_Score", "Anomaly_Level",
    ]
    result = scored[cols].sort_values("Anomaly_Score", ascending=False)

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = OUT_DIR / "ml_anomaly_detection.xlsx"
    result.to_excel(out_path, index=False)
    logger.info("saved %s", out_path)


if __name__ == "__main__":
    main()
