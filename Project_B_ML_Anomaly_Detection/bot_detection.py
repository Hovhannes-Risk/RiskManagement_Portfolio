"""
Low-volume sharp-player detector.

Flags profitable accounts with <= 20 settled bets — the classic sharp
signature documented in Documentation/findings_summary.md §2. Shares its
aggregation and detection primitives with the rest of the portfolio via
the unit-tested `risk_core` package.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).parent
PORTFOLIO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PORTFOLIO_ROOT))

from risk_core import player_stats  # noqa: E402

# Shared anonymized sample (single source of truth across all projects).
# In production this script points at the daily book export instead.
DATA_PATH = PORTFOLIO_ROOT / "Project_A_Dashboard" / "sample_data" / "mydata_sample.xlsx"
# sample_output/ holds curated results from the full 526k-bet dataset.
# Live runs against the public sample write to outputs/ (gitignored).
OUT_DIR = SCRIPT_DIR / "outputs"

LOW_VOLUME_THRESHOLD = 20

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("bot_detection")


def load_bets(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load the bet-level frame; tolerate the public sample's missing bet_type."""
    bets = pd.read_excel(path, sheet_name="Raw_Data")
    if "bet_type" not in bets.columns:
        # Public sample ships without the bet_type column (singles only);
        # the production dataset distinguishes Ordinar / Express.
        bets["bet_type"] = "Ordinar"
    logger.info("loaded %d bets from %s", len(bets), path.name)
    return bets


def low_volume_winners(bets: pd.DataFrame, max_bets: int = LOW_VOLUME_THRESHOLD) -> pd.DataFrame:
    """Profitable players with <= max_bets settled bets, enriched and ranked.

    ROI / win-rate come vectorised from `risk_core.player_stats` — no
    per-player rescans of the bet-level frame.
    """
    stats = player_stats(bets)
    winners = stats[(stats["Total_Bets"] <= max_bets) & (stats["Player_Profit"] > 0)].copy()

    sport_mix = (
        bets[bets["bettor"].isin(winners["bettor"])]
        .groupby("bettor")
        .agg(
            Sports_Played=("sports", lambda x: ", ".join(sorted(x.unique()))),
            Most_Played_Sport=("sports", lambda x: x.mode().iloc[0] if len(x) else "N/A"),
            Markets_Used=("market", "nunique"),
            Ordinar_Count=("bet_type", lambda x: int((x == "Ordinar").sum())),
            Express_Count=("bet_type", lambda x: int((x == "Express").sum())),
        )
        .reset_index()
    )
    report = winners.merge(sport_mix, on="bettor", how="left")
    return report.sort_values("Player_Profit", ascending=False).reset_index(drop=True)


def main() -> None:
    bets = load_bets()
    report = low_volume_winners(bets)

    logger.info("found %d winning players with <=%d bets", len(report), LOW_VOLUME_THRESHOLD)
    print("\nTOP 10 WINNING PLAYERS (<=20 bets):")
    print(report[["bettor", "Total_Bets", "Player_Profit", "Win_Rate", "ROI_pct"]].head(10))
    print("\nTOTAL STATS:")
    print(f"Total Players: {len(report)}")
    print(f"House loss to this cohort: ${report['Player_Profit'].sum():,.2f}")
    print(f"Avg Profit per Player: ${report['Player_Profit'].mean():,.2f}")
    print(f"Avg Win Rate: {report['Win_Rate'].mean():.1f}%")

    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = OUT_DIR / "winning_low_volume_players.xlsx"
    report.to_excel(out_path, index=False)
    logger.info("saved %s", out_path)


if __name__ == "__main__":
    main()
