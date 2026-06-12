"""Unit tests for risk_core.metrics — the invariants a risk desk relies on."""

import numpy as np
import pandas as pd
import pytest

from risk_core import avg_won_odds, hold_pct, player_stats, wilson_ci


# ---------------------------------------------------------------- avg_won_odds
def test_avg_won_odds_never_below_one():
    """Decimal odds are bounded below by 1.0 — the methodology.md §2 invariant."""
    won = pd.Series([1.5, 0.4, 2.02, 0.01])  # net multipliers of winning bets
    value = avg_won_odds(won)
    assert value is not None
    assert value >= 1.0


def test_avg_won_odds_matches_methodology_worked_example():
    """Player P3 from methodology.md §2: sum 4.97 over 4 wins -> 2.24."""
    won = pd.Series([4.97 / 4] * 4)  # same mean as the worked example
    assert avg_won_odds(won) == pytest.approx(4.97 / 4 + 1, abs=1e-9)


def test_avg_won_odds_empty_returns_none():
    assert avg_won_odds(pd.Series([], dtype=float)) is None


# ---------------------------------------------------------------- wilson_ci
def test_wilson_ci_bounds_within_0_100():
    for successes, n in [(0, 10), (10, 10), (354, 469), (1, 1), (0, 1)]:
        low, high = wilson_ci(successes, n)
        assert 0.0 <= low <= high <= 100.0


def test_wilson_ci_zero_n_is_safe():
    assert wilson_ci(0, 0) == (0.0, 0.0)


def test_wilson_ci_published_league_finding():
    """The UEFA Youth League finding: 344/444 wins -> lower bound above 73%.

    This is the statistical core of findings_summary.md §3; if this bound
    ever drops below the 55% operational threshold the finding dies.
    """
    low, high = wilson_ci(344, 444)
    assert low > 73.0
    assert high < 82.0
    # survives the Bonferroni-style correction documented in methodology §9
    low_b, _ = wilson_ci(344, 444, z=3.29)
    assert low_b > 70.0


# ---------------------------------------------------------------- hold_pct
def test_hold_pct_zero_turnover():
    assert hold_pct(100.0, 0.0) == 0.0


def test_hold_pct_sign_follows_ggr():
    assert hold_pct(-585.0, 20168.0) < 0
    assert hold_pct(585.0, 20168.0) > 0


# ---------------------------------------------------------------- player_stats
@pytest.fixture
def tiny_book() -> pd.DataFrame:
    """Two players: P1 loses to the house, P2 beats it."""
    return pd.DataFrame(
        {
            "bet_id": [1, 2, 3, 4],
            "bettor": ["P1", "P1", "P2", "P2"],
            "usd_amount": [100.0, 100.0, 50.0, 50.0],
            "usd_ggr": [100.0, 100.0, -75.0, 50.0],  # house view
        }
    )


def test_player_stats_profit_sign_convention(tiny_book):
    stats = player_stats(tiny_book).set_index("bettor")
    assert stats.loc["P1", "Player_Profit"] == -200.0  # player lost
    assert stats.loc["P2", "Player_Profit"] == 25.0  # player won net


def test_player_stats_roi_vectorised_consistency(tiny_book):
    """ROI from the aggregate must equal the naive per-player computation."""
    stats = player_stats(tiny_book).set_index("bettor")
    naive_p2 = (-tiny_book[tiny_book.bettor == "P2"].usd_ggr.sum()) / 100.0 * 100.0
    assert stats.loc["P2", "ROI_pct"] == pytest.approx(naive_p2)


def test_player_stats_rejects_missing_columns():
    with pytest.raises(ValueError, match="missing required columns"):
        player_stats(pd.DataFrame({"bettor": ["P1"]}))
