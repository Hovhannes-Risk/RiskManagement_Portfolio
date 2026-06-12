"""
Regulated-market compliance engine (MGA / UKGC world, synthetic data).

Five typed rules, each emitting an Alert with severity, the evidence
that fired it, and a recommended action expressed in regulated-market
vocabulary (EDD review, RG interaction levels, safer-gambling tooling).
The engine is deliberately conservative in the same way the rest of
this portfolio is: alerts route to HUMAN review queues — the engine
never blocks, limits, or contacts a player by itself.

Design notes
------------
- Thresholds live in a single CONFIG dict so a compliance officer can
  re-tune them without touching rule logic.
- Every rule is a pure function frame -> list[Alert]; rules are
  independently unit-tested in tests/test_compliance.py against the
  planted patterns in the synthetic generator.
- Severity vocabulary intentionally mirrors the risk projects
  (CRITICAL / HIGH / MEDIUM) so one escalation queue can carry both.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).parent
DATA_PATH = SCRIPT_DIR / "sample_data" / "synthetic_players.xlsx"
OUT_DIR = SCRIPT_DIR / "sample_output"

CONFIG: dict[str, float] = {
    # AML — structuring
    "edd_threshold_eur": 2000.0,       # enhanced-due-diligence trigger
    "structuring_band_pct": 0.10,      # deposits within 10% below threshold
    "structuring_window_hours": 72.0,
    "structuring_min_count": 3,
    # RG — loss chasing
    "chasing_redeposit_minutes": 10.0,
    "chasing_min_cycles": 3,
    # RG — night escalation
    "night_start_hour": 0,
    "night_end_hour": 5,
    "night_min_sessions": 4,
    # RG — withdrawal reversal
    "reversal_min_count": 2,
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("compliance_engine")


@dataclass
class Alert:
    player_id: str
    rule: str
    severity: str           # CRITICAL / HIGH / MEDIUM
    evidence: str
    recommended_action: str
    framework_ref: str      # which regulated-market obligation this maps to
    details: dict = field(default_factory=dict)


# --------------------------------------------------------------------- rules
def rule_structuring(deposits: pd.DataFrame, cfg: dict = CONFIG) -> list[Alert]:
    """Repeated deposits just under the EDD threshold in a short window.

    Maps to the AML obligation to detect threshold-avoidance behaviour.
    Output is an internal escalation to the MLRO review queue — the
    engine itself never files anything externally.
    """
    alerts: list[Alert] = []
    lo = cfg["edd_threshold_eur"] * (1.0 - cfg["structuring_band_pct"])
    hi = cfg["edd_threshold_eur"]
    band = deposits[(deposits["amount_eur"] >= lo) & (deposits["amount_eur"] < hi)].copy()
    band["ts"] = pd.to_datetime(band["ts"])

    for pid, g in band.groupby("player_id"):
        g = g.sort_values("ts")
        window = pd.Timedelta(hours=cfg["structuring_window_hours"])
        # count the densest window
        best = max(
            (int(((g["ts"] >= t) & (g["ts"] <= t + window)).sum()) for t in g["ts"]),
            default=0,
        )
        if best >= cfg["structuring_min_count"]:
            alerts.append(Alert(
                player_id=pid,
                rule="AML_STRUCTURING",
                severity="CRITICAL",
                evidence=(f"{best} deposits in the {lo:.0f}-{hi:.0f} EUR band "
                          f"inside {cfg['structuring_window_hours']:.0f}h"),
                recommended_action=("Freeze nothing; escalate to MLRO review queue "
                                    "with full deposit timeline. EDD documentation "
                                    "request only after MLRO sign-off."),
                framework_ref="AML threshold-avoidance monitoring",
                details={"window_count": best},
            ))
    return alerts


def rule_loss_chasing(bets: pd.DataFrame, deposits: pd.DataFrame,
                      cfg: dict = CONFIG) -> list[Alert]:
    """Deposit within N minutes of a losing bet, repeated, with stake escalation."""
    alerts: list[Alert] = []
    b = bets.copy(); b["ts"] = pd.to_datetime(b["ts"])
    d = deposits.copy(); d["ts"] = pd.to_datetime(d["ts"])
    losses = b[b["ggr_eur"] > 0]  # house won => player lost

    for pid, lg in losses.groupby("player_id"):
        pdep = d[d["player_id"] == pid]
        if pdep.empty:
            continue
        cycles = 0
        chased_stakes: list[float] = []
        for _, loss in lg.iterrows():
            gap = (pdep["ts"] - loss["ts"]).dt.total_seconds() / 60.0
            if ((gap > 0) & (gap <= cfg["chasing_redeposit_minutes"])).any():
                cycles += 1
                chased_stakes.append(float(loss["stake_eur"]))
        escalating = len(chased_stakes) >= 2 and chased_stakes[-1] > chased_stakes[0]
        if cycles >= cfg["chasing_min_cycles"]:
            alerts.append(Alert(
                player_id=pid,
                rule="RG_LOSS_CHASING",
                severity="HIGH" if escalating else "MEDIUM",
                evidence=(f"{cycles} loss->redeposit cycles within "
                          f"{cfg['chasing_redeposit_minutes']:.0f} min"
                          + ("; stakes escalating" if escalating else "")),
                recommended_action=("Route to RG team for a tier-2 safer-gambling "
                                    "interaction; surface deposit-limit and "
                                    "time-out tooling in next session."),
                framework_ref="Customer-interaction obligation (markers of harm)",
                details={"cycles": cycles, "escalating": escalating},
            ))
    return alerts


def rule_night_escalation(sessions: pd.DataFrame, cfg: dict = CONFIG) -> list[Alert]:
    """Rising count and length of 00:00-05:00 sessions."""
    alerts: list[Alert] = []
    s = sessions.copy(); s["start_ts"] = pd.to_datetime(s["start_ts"])
    night = s[(s["start_ts"].dt.hour >= cfg["night_start_hour"])
              & (s["start_ts"].dt.hour < cfg["night_end_hour"])]
    for pid, g in night.groupby("player_id"):
        if len(g) >= cfg["night_min_sessions"]:
            g = g.sort_values("start_ts")
            first_half = g["duration_min"].iloc[: max(1, len(g) // 2)].mean()
            second_half = g["duration_min"].iloc[len(g) // 2:].mean()
            escalating = second_half > first_half * 1.25
            alerts.append(Alert(
                player_id=pid,
                rule="RG_NIGHT_ESCALATION",
                severity="HIGH" if escalating else "MEDIUM",
                evidence=(f"{len(g)} night sessions (00-05h); avg duration "
                          f"{first_half:.0f} -> {second_half:.0f} min"),
                recommended_action=("Add to RG watchlist; if pattern persists one "
                                    "more week, schedule a safer-gambling "
                                    "interaction and offer reality checks."),
                framework_ref="Markers of harm — time-of-play pattern",
                details={"night_sessions": int(len(g))},
            ))
    return alerts


def rule_withdrawal_reversal(withdrawals: pd.DataFrame, cfg: dict = CONFIG) -> list[Alert]:
    """Cancelled withdrawals re-staked — a core marker of harm."""
    alerts: list[Alert] = []
    if withdrawals.empty:
        return alerts
    cancelled = withdrawals[withdrawals["status"] == "CANCELLED"]
    for pid, g in cancelled.groupby("player_id"):
        if len(g) >= cfg["reversal_min_count"]:
            alerts.append(Alert(
                player_id=pid,
                rule="RG_WITHDRAWAL_REVERSAL",
                severity="HIGH",
                evidence=f"{len(g)} withdrawal requests cancelled and re-staked",
                recommended_action=("Disable one-click withdrawal cancellation for "
                                    "this account pending RG review; proactive "
                                    "safer-gambling contact."),
                framework_ref="Markers of harm — withdrawal reversal",
                details={"cancelled_count": int(len(g))},
            ))
    return alerts


# -------------------------------------------------------------------- engine
def run_engine(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    alerts: list[Alert] = []
    alerts += rule_structuring(frames["deposits"])
    alerts += rule_loss_chasing(frames["bets"], frames["deposits"])
    alerts += rule_night_escalation(frames["sessions"])
    alerts += rule_withdrawal_reversal(frames["withdrawals"])

    queue = pd.DataFrame([a.__dict__ for a in alerts])
    if not queue.empty:
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
        queue = queue.sort_values(
            ["severity", "player_id"], key=lambda c: c.map(severity_order) if c.name == "severity" else c
        ).reset_index(drop=True)
    logger.info("engine produced %d alerts", len(queue))
    return queue


def load_frames(path: Path = DATA_PATH) -> dict[str, pd.DataFrame]:
    xl = pd.ExcelFile(path)
    return {name: xl.parse(name) for name in xl.sheet_names}


def main() -> None:
    if not DATA_PATH.exists():
        logger.info("synthetic data not found — generating it first")
        from generate_synthetic_data import main as gen_main
        gen_main()

    frames = load_frames()
    queue = run_engine(frames)

    print("\nESCALATION QUEUE (synthetic data):")
    if queue.empty:
        print("  no alerts")
    else:
        print(queue[["player_id", "rule", "severity", "evidence"]].to_string(index=False))
        print(f"\nTotal alerts: {len(queue)} | "
              f"CRITICAL: {(queue['severity']=='CRITICAL').sum()} | "
              f"HIGH: {(queue['severity']=='HIGH').sum()} | "
              f"MEDIUM: {(queue['severity']=='MEDIUM').sum()}")

    os.makedirs(OUT_DIR, exist_ok=True)
    out = OUT_DIR / "escalation_queue.xlsx"
    queue.drop(columns=["details"], errors="ignore").to_excel(out, index=False)
    logger.info("saved %s", out)


if __name__ == "__main__":
    main()
