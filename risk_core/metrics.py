"""
Core risk metrics.

Conventions used throughout the portfolio:
- `usd_ggr` is from the house perspective: positive = house won.
- `resolved_odds` is the NET return multiplier (decimal_odds - 1 on a win,
  0.00 on a loss). See Documentation/methodology.md §2 for the discovery
  that motivated `avg_won_odds`.
- Decimal odds are bounded below by 1.0; any odds metric returning a value
  below 1.0 indicates a field-semantics bug, not a market reality.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def avg_won_odds(resolved_odds_won: pd.Series) -> float | None:
    """Average decimal odds over WON bets only.

    Implements the corrected formula from methodology.md §2:
        Avg_Won_Odds = mean(resolved_odds + 1) over won bets only

    Parameters
    ----------
    resolved_odds_won : net return multipliers of winning bets only.

    Returns
    -------
    Mean decimal odds (always >= 1.0), or None when no won bets exist.
    """
    if len(resolved_odds_won) == 0:
        return None
    value = float((resolved_odds_won.astype(float) + 1.0).mean())
    if value < 1.0:
        # Defensive: this can only happen if a lost/cancelled bet leaked in.
        logger.warning(
            "avg_won_odds=%.4f is below 1.0 — input likely contains "
            "non-winning bets; check the subbet_result filter upstream.",
            value,
        )
    return value


def hold_pct(ggr: float, turnover: float) -> float:
    """House hold percentage; 0.0 when turnover is zero."""
    return (ggr / turnover * 100.0) if turnover else 0.0


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score 95% confidence interval for a binomial proportion.

    Returns (low, high) in PERCENT, both clamped to [0, 100].
    Preferred over the normal approximation for the small-n league
    samples this portfolio scores (see methodology.md §6).
    """
    if n <= 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1.0 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt((p * (1.0 - p) + z**2 / (4 * n)) / n) / denom
    return (max(0.0, (centre - half) * 100.0), min(100.0, (centre + half) * 100.0))


def player_stats(bets: pd.DataFrame) -> pd.DataFrame:
    """Per-player aggregation used across Projects B, C and D.

    Expects columns: bettor, bet_id, usd_amount, usd_ggr.
    Returns one row per bettor with:
        Total_Bets, Total_Stake, Avg_Stake, Total_GGR,
        Player_Profit (= -Total_GGR), Win_Rate (settled-GGR sign proxy),
        ROI_pct (player profit / stake).

    ROI is computed vectorised from the aggregate — NOT by re-scanning the
    bet-level frame per player (the O(n x players) anti-pattern the first
    version of bot_detection.py contained).
    """
    required = {"bettor", "bet_id", "usd_amount", "usd_ggr"}
    missing = required - set(bets.columns)
    if missing:
        raise ValueError(f"player_stats: missing required columns {sorted(missing)}")

    stats = (
        bets.groupby("bettor")
        .agg(
            Total_Bets=("bet_id", "count"),
            Total_Stake=("usd_amount", "sum"),
            Avg_Stake=("usd_amount", "mean"),
            Total_GGR=("usd_ggr", "sum"),
            Winning_Bets=("usd_ggr", lambda s: int((s < 0).sum())),
        )
        .reset_index()
    )
    stats["Player_Profit"] = -stats["Total_GGR"]
    stats["Win_Rate"] = np.where(
        stats["Total_Bets"] > 0, stats["Winning_Bets"] / stats["Total_Bets"] * 100.0, 0.0
    )
    stats["ROI_pct"] = np.where(
        stats["Total_Stake"] > 0,
        stats["Player_Profit"] / stats["Total_Stake"] * 100.0,
        0.0,
    )
    logger.info("player_stats: aggregated %d bets into %d players", len(bets), len(stats))
    return stats
