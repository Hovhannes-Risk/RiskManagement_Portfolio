"""
risk_core — shared analytical primitives for the Risk Management Portfolio.

Single source of truth for the metrics and detection logic that the
individual projects (B, C, D, E) previously duplicated. Every function
here is unit-tested in /tests and exercised by CI on every push.
"""

from risk_core.metrics import avg_won_odds, hold_pct, player_stats, wilson_ci
from risk_core.detection import anomaly_level, same_second_suspects

__all__ = [
    "avg_won_odds",
    "hold_pct",
    "player_stats",
    "wilson_ci",
    "anomaly_level",
    "same_second_suspects",
]
