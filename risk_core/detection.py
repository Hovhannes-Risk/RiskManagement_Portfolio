"""
Detection primitives: same-second bot signal and anomaly-score banding.

Both are SURVEILLANCE signals, not account actions — see
Documentation/methodology.md §3 and §10 (false-positive classes).
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

ANOMALY_BANDS: dict[int, str] = {3: "CRITICAL", 2: "HIGH", 1: "MEDIUM", 0: "NORMAL"}


def anomaly_level(score: int) -> str:
    """Map the 0-3 ensemble anomaly score to its operational band.

    Raises ValueError outside {0,1,2,3} — an out-of-range score means the
    ensemble upstream is miscounting flags, which must fail loudly.
    """
    if score not in ANOMALY_BANDS:
        raise ValueError(f"anomaly score must be in 0..3, got {score!r}")
    return ANOMALY_BANDS[score]


def same_second_suspects(
    bets: pd.DataFrame,
    time_col: str = "bet_time",
    account_col: str = "bettor",
    min_bets_per_second: int = 2,
    distinct_markets_only: bool = False,
) -> list[str]:
    """Accounts placing >= `min_bets_per_second` bets inside one second.

    Operational definition documented in methodology.md §3. Manual
    placement (read market -> select -> stake -> confirm) takes 2-4s
    end-to-end, so repeated same-second placement is a scripted-behaviour
    indicator.

    `distinct_markets_only=True` applies the stricter layer-2 definition
    that excludes the main false-positive class (multi-leg / split slips
    submitted as one batch — see methodology.md §10): the bets must land
    on DIFFERENT markets within the same second to count.

    Returns a sorted list of account identifiers.
    """
    d = bets.dropna(subset=[time_col]).copy()
    d["_sec"] = pd.to_datetime(d[time_col], errors="coerce").dt.floor("s")
    d = d.dropna(subset=["_sec"])

    if distinct_markets_only and "market" in d.columns:
        grouped = d.groupby([account_col, "_sec"])["market"].nunique()
    else:
        grouped = d.groupby([account_col, "_sec"]).size()

    suspects = sorted(
        grouped[grouped >= min_bets_per_second].reset_index()[account_col].unique().tolist()
    )
    logger.info(
        "same_second_suspects: %d accounts flagged (threshold=%d, distinct_markets=%s)",
        len(suspects),
        min_bets_per_second,
        distinct_markets_only,
    )
    return suspects
