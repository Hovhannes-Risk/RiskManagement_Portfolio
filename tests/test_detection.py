"""Tests for risk_core.detection plus a schema gate on the shipped sample."""

from pathlib import Path

import pandas as pd
import pytest

from risk_core import anomaly_level, same_second_suspects

PORTFOLIO_ROOT = Path(__file__).parent.parent
SAMPLE = PORTFOLIO_ROOT / "Project_A_Dashboard" / "sample_data" / "mydata_sample.xlsx"


# ------------------------------------------------------------ anomaly_level
def test_anomaly_level_full_band_mapping():
    assert anomaly_level(0) == "NORMAL"
    assert anomaly_level(1) == "MEDIUM"
    assert anomaly_level(2) == "HIGH"
    assert anomaly_level(3) == "CRITICAL"


def test_anomaly_level_rejects_out_of_range():
    for bad in (-1, 4, 99):
        with pytest.raises(ValueError):
            anomaly_level(bad)


# ------------------------------------------------------ same_second_suspects
def _synthetic_book() -> pd.DataFrame:
    """One scripted account (BOT: 3 bets in one second, 2 markets),
    one human (HUM: bets seconds apart), one batch-slip case (SLIP:
    2 same-second bets on the SAME market — the multi-leg false-positive
    class from methodology.md §10)."""
    return pd.DataFrame(
        {
            "bettor": ["BOT", "BOT", "BOT", "HUM", "HUM", "SLIP", "SLIP"],
            "bet_time": [
                "2026-05-20 10:00:00.10",
                "2026-05-20 10:00:00.55",
                "2026-05-20 10:00:00.90",
                "2026-05-20 10:00:01",
                "2026-05-20 10:00:07",
                "2026-05-20 11:00:00.20",
                "2026-05-20 11:00:00.80",
            ],
            "market": ["FTR", "Over/Under", "FTR", "FTR", "FTR", "FTR", "FTR"],
        }
    )


def test_bot_flagged_human_not():
    suspects = same_second_suspects(_synthetic_book())
    assert "BOT" in suspects
    assert "HUM" not in suspects


def test_distinct_market_layer_clears_batch_slips():
    """Layer-2 definition drops the batch-slip false positive but keeps the bot."""
    loose = same_second_suspects(_synthetic_book())
    strict = same_second_suspects(_synthetic_book(), distinct_markets_only=True)
    assert "SLIP" in loose  # layer-1 surveillance signal fires
    assert "SLIP" not in strict  # layer-2 clears it
    assert "BOT" in strict  # cross-market same-second still flagged


def test_handles_missing_timestamps():
    book = _synthetic_book()
    book.loc[0, "bet_time"] = None
    suspects = same_second_suspects(book)  # must not raise
    assert isinstance(suspects, list)


# ------------------------------------------------------------- sample schema
REQUIRED_COLUMNS = {
    "bet_id", "bettor", "bet_time", "sports", "league", "market",
    "usd_amount", "usd_ggr", "odds", "resolved_odds", "subbet_result",
}


@pytest.mark.skipif(not SAMPLE.exists(), reason="public sample not present")
def test_shipped_sample_schema_and_anonymization():
    df = pd.read_excel(SAMPLE, sheet_name="Raw_Data")
    assert REQUIRED_COLUMNS.issubset(df.columns)
    # Every account identifier must be a synthetic P-ID — never anything resembling a real wallet/account handle.
    bettors = df["bettor"].astype(str)
    assert bettors.str.startswith("P").all()
    assert not bettors.str.startswith("0x").any()
    # Stakes must be non-negative; odds (decimal) bounded below by 1.
    assert (df["usd_amount"] >= 0).all()
    assert (df["odds"] >= 1.0).all()
