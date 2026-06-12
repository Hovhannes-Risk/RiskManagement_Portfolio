"""Tests for the Project E compliance engine.

The synthetic generator plants known patterns with a hidden `_planted`
label; the engine must recover them (recall) without flooding the queue
with clean players (precision).
"""

import sys
from pathlib import Path

import pytest

PORTFOLIO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PORTFOLIO_ROOT / "Project_E_Regulated_Compliance"))

from generate_synthetic_data import generate  # noqa: E402
from compliance_engine import run_engine  # noqa: E402

RULE_FOR_LABEL = {
    "STRUCTURING": "AML_STRUCTURING",
    "LOSS_CHASING": "RG_LOSS_CHASING",
    "NIGHT_ESCALATION": "RG_NIGHT_ESCALATION",
    "WITHDRAWAL_REVERSAL": "RG_WITHDRAWAL_REVERSAL",
}


@pytest.fixture(scope="module")
def frames():
    return generate(n_clean=60, n_each_pattern=5)


@pytest.fixture(scope="module")
def queue(frames):
    return run_engine(frames)


def test_engine_recall_per_pattern(frames, queue):
    """Every planted pattern class must be recovered at >= 80% recall."""
    players = frames["players"]
    for label, rule in RULE_FOR_LABEL.items():
        planted = set(players[players["_planted"] == label]["player_id"])
        flagged = set(queue[queue["rule"] == rule]["player_id"])
        recall = len(planted & flagged) / len(planted)
        assert recall >= 0.8, f"{label}: recall {recall:.0%} below 80%"


def test_engine_precision_on_clean_players(frames, queue):
    """Clean players must stay out of the queue (<= 5% false-positive rate)."""
    players = frames["players"]
    clean = set(players[players["_planted"] == "CLEAN"]["player_id"])
    flagged_clean = clean & set(queue["player_id"])
    fp_rate = len(flagged_clean) / len(clean)
    assert fp_rate <= 0.05, f"false-positive rate on clean players: {fp_rate:.0%}"


def test_structuring_alerts_are_critical(queue):
    s = queue[queue["rule"] == "AML_STRUCTURING"]
    assert not s.empty
    assert (s["severity"] == "CRITICAL").all()


def test_every_alert_carries_action_and_framework_ref(queue):
    assert (queue["recommended_action"].str.len() > 0).all()
    assert (queue["framework_ref"].str.len() > 0).all()
