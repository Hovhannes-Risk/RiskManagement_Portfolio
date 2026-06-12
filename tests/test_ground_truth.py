"""Ground-truth recall tests — the reason this dataset is synthetic.

The generator plants patterns at known account ranges; these tests prove
the detection stack recovers them. They require the full dataset
(data_generator/full_dataset.parquet), which CI regenerates before the
test step; locally, run the generator once first or the tests skip.

Planted ID ranges (see data_generator/generate_sportsbook_data.py):
    P00001-P11553  recreational mass
    P11554-P12013  scripted same-second accounts (460)
    P12014-P12108  low-volume sharp profiles (95)
    P12109-P12168  insider-style Youth League group (60)
    P12169-P12208  coordinated pairs (20 pairs / 40 accounts)
"""

from pathlib import Path

import pandas as pd
import pytest

from risk_core import player_stats, same_second_suspects, wilson_ci

PARQUET = Path(__file__).parent.parent / "data_generator" / "full_dataset.parquet"

pytestmark = pytest.mark.skipif(not PARQUET.exists(),
                                reason="full dataset not generated (run data_generator first)")


@pytest.fixture(scope="module")
def full():
    return pd.read_parquet(PARQUET)


def _ids(a: int, b: int) -> set[str]:
    return {f"P{i:05d}" for i in range(a, b + 1)}


def test_bot_recall_is_total(full):
    """Every planted scripted account must be flagged."""
    flagged = set(same_second_suspects(full))
    planted = _ids(11554, 12013)
    assert planted <= flagged
    # contamination stays tiny: coincidental same-second placements only
    assert len(flagged - planted) <= 10


def test_sharp_recall_above_75pct(full):
    """Planted +EV profiles must dominate the low-volume winner cohort."""
    ps = player_stats(full)
    winners = set(ps[(ps.Total_Bets <= 20) & (ps.Player_Profit > 0)]["bettor"])
    planted = _ids(12014, 12108)
    recall = len(planted & winners) / len(planted)
    assert recall >= 0.75  # the rest lose to variance — by design


def test_insider_league_signal_survives_correction(full):
    """The planted thin-league group must clear the corrected Wilson bound."""
    yl = full[(full.league == "UEFA Youth League")
              & (full.subbet_result.isin(["won", "lost"]))]
    wins, n = int((yl.usd_ggr < 0).sum()), len(yl)
    low, _ = wilson_ci(wins, n, z=3.29)  # Bonferroni-style, methodology §9
    assert n >= 300
    assert low > 60.0


def test_dataset_shape_is_canonical(full):
    assert len(full) == 526_232
    assert full.bettor.nunique() == 12_208
    assert full.sports.nunique() == 19
