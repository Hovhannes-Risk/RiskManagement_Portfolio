"""
Synthetic data generator for the regulated-market compliance layer.

EVERYTHING THIS SCRIPT PRODUCES IS SYNTHETIC. No real player, deposit,
or transaction appears anywhere in Project E — by design: AML and
responsible-gambling cases cannot be published even anonymized, so this
project openly trades realism of individuals for realism of PATTERNS.

The generator embeds five compliance patterns at known rates, so the
rules engine's recall is verifiable (every planted case carries a
hidden `_planted` label used only by the test suite):

  1. STRUCTURING   — repeated deposits just under the 2,000 EUR
                     enhanced-due-diligence threshold within 72h.
  2. LOSS_CHASING  — deposit within 10 minutes of a large losing bet,
                     escalating stake sizes.
  3. NIGHT_ESCALATION — session start times drifting into 00:00-05:00
                     with rising session length.
  4. WITHDRAWAL_REVERSAL — requested withdrawals cancelled and re-staked
                     within 24h (a core RG marker).
  5. CLEAN         — recreational baseline behaviour.

Output: synthetic_players.xlsx (players, deposits, withdrawals, bets,
sessions sheets) consumed by compliance_engine.py.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).parent
OUT_PATH = SCRIPT_DIR / "sample_data" / "synthetic_players.xlsx"

RNG = np.random.default_rng(42)
BASE = datetime(2026, 5, 1)
EDD_THRESHOLD_EUR = 2000.0

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("synthetic_generator")


def _clean_player(pid: str) -> dict:
    deposits, bets, withdrawals, sessions = [], [], [], []
    for d in range(RNG.integers(3, 8)):
        t = BASE + timedelta(days=int(RNG.integers(0, 28)), hours=int(RNG.integers(10, 22)))
        deposits.append({"player_id": pid, "ts": t, "amount_eur": float(RNG.uniform(20, 300))})
    for b in range(RNG.integers(10, 60)):
        t = BASE + timedelta(days=int(RNG.integers(0, 28)), hours=int(RNG.integers(10, 23)),
                             minutes=int(RNG.integers(0, 59)))
        stake = float(RNG.uniform(5, 80))
        bets.append({"player_id": pid, "ts": t, "stake_eur": stake,
                     "ggr_eur": stake * float(RNG.uniform(-1.0, 0.25))})
    for s in range(RNG.integers(5, 15)):
        start = BASE + timedelta(days=int(RNG.integers(0, 28)), hours=int(RNG.integers(11, 21)))
        sessions.append({"player_id": pid, "start_ts": start,
                         "duration_min": int(RNG.integers(10, 90))})
    return {"deposits": deposits, "bets": bets, "withdrawals": withdrawals,
            "sessions": sessions, "label": "CLEAN"}


def _structuring_player(pid: str) -> dict:
    base = _clean_player(pid)
    burst_start = BASE + timedelta(days=int(RNG.integers(5, 20)))
    for i in range(int(RNG.integers(4, 7))):
        t = burst_start + timedelta(hours=int(RNG.integers(0, 70)))
        # consistently just under the EDD threshold
        amount = float(EDD_THRESHOLD_EUR - RNG.uniform(20, 180))
        base["deposits"].append({"player_id": pid, "ts": t, "amount_eur": amount})
    base["label"] = "STRUCTURING"
    return base


def _loss_chasing_player(pid: str) -> dict:
    base = _clean_player(pid)
    t = BASE + timedelta(days=int(RNG.integers(3, 22)), hours=19)
    stake = 150.0
    for cycle in range(5):
        base["bets"].append({"player_id": pid, "ts": t, "stake_eur": stake,
                             "ggr_eur": stake})  # player loses (house wins)
        t_dep = t + timedelta(minutes=int(RNG.integers(2, 9)))
        base["deposits"].append({"player_id": pid, "ts": t_dep,
                                 "amount_eur": stake * 1.6})
        t = t_dep + timedelta(minutes=int(RNG.integers(3, 15)))
        stake *= 1.7  # escalation
    base["label"] = "LOSS_CHASING"
    return base


def _night_escalation_player(pid: str) -> dict:
    base = _clean_player(pid)
    for week in range(4):
        start_hour = max(0, 23 - week * 0)  # sessions drift into the night
        for n in range(2 + week):
            start = BASE + timedelta(days=week * 7 + int(RNG.integers(0, 6)),
                                     hours=int(RNG.integers(0, 5)))
            base["sessions"].append({"player_id": pid, "start_ts": start,
                                     "duration_min": int(60 + week * 45 + RNG.integers(0, 30))})
    base["label"] = "NIGHT_ESCALATION"
    return base


def _withdrawal_reversal_player(pid: str) -> dict:
    base = _clean_player(pid)
    for r in range(int(RNG.integers(3, 5))):
        t = BASE + timedelta(days=int(RNG.integers(2, 25)), hours=int(RNG.integers(12, 20)))
        amount = float(RNG.uniform(200, 900))
        base["withdrawals"].append({"player_id": pid, "ts": t, "amount_eur": amount,
                                    "status": "CANCELLED",
                                    "cancelled_ts": t + timedelta(hours=int(RNG.integers(1, 20)))})
        base["bets"].append({"player_id": pid,
                             "ts": t + timedelta(hours=int(RNG.integers(2, 22))),
                             "stake_eur": amount * 0.9, "ggr_eur": amount * 0.5})
    base["withdrawals"].append({"player_id": pid, "ts": BASE + timedelta(days=27),
                                "amount_eur": 150.0, "status": "PAID", "cancelled_ts": None})
    base["label"] = "WITHDRAWAL_REVERSAL"
    return base


def generate(n_clean: int = 60, n_each_pattern: int = 5) -> dict[str, pd.DataFrame]:
    builders = [_structuring_player, _loss_chasing_player,
                _night_escalation_player, _withdrawal_reversal_player]
    players, deposits, withdrawals, bets, sessions = [], [], [], [], []
    pid_counter = 1

    def add(record: dict, pid: str) -> None:
        players.append({"player_id": pid, "_planted": record["label"],
                        "registered": BASE - timedelta(days=int(RNG.integers(30, 400)))})
        deposits.extend(record["deposits"])
        withdrawals.extend(record["withdrawals"])
        bets.extend(record["bets"])
        sessions.extend(record["sessions"])

    for _ in range(n_clean):
        pid = f"S{pid_counter:04d}"; pid_counter += 1
        add(_clean_player(pid), pid)
    for builder in builders:
        for _ in range(n_each_pattern):
            pid = f"S{pid_counter:04d}"; pid_counter += 1
            add(builder(pid), pid)

    frames = {
        "players": pd.DataFrame(players),
        "deposits": pd.DataFrame(deposits).sort_values("ts"),
        "withdrawals": pd.DataFrame(withdrawals),
        "bets": pd.DataFrame(bets).sort_values("ts"),
        "sessions": pd.DataFrame(sessions).sort_values("start_ts"),
    }
    logger.info("generated %d players (%d planted across 4 patterns)",
                len(players), 4 * n_each_pattern)
    return frames


def main() -> None:
    frames = generate()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUT_PATH) as writer:
        for name, frame in frames.items():
            frame.to_excel(writer, sheet_name=name, index=False)
    logger.info("saved %s", OUT_PATH)


if __name__ == "__main__":
    main()
