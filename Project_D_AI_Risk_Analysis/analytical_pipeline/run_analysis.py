"""
Analytical pipeline for AI-assisted weekly risk analysis.

Senior-level design principle:
  Do not feed raw bet-level data to an LLM. Pre-process numerically
  in Python, hand the LLM a *structured brief* with confidence
  intervals and sample-size flags already attached. The LLM's job is
  synthesis and narrative, not arithmetic.

Pipeline:
  1. Load anonymized weekly sample (Project_A's mydata_sample.xlsx)
  2. Compute KPIs across multiple dimensions
  3. Apply the methodology's `Avg_Won_Odds = mean(resolved_odds + 1)`
     over won bets only — the field-integrity fix documented in
     Documentation/methodology.md §2
  4. Compute player-level scores with explicit sample-size flags
  5. Detect bot suspects (same-second placement) and behavioral
     fingerprint candidates
  6. Compute market-level P&L breakdowns
  7. Emit a JSON brief that downstream prompts consume

Output:
  analytical_brief.json — single source of truth for every prompt run
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from collections import Counter

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent
PORTFOLIO_ROOT = SCRIPT_DIR.parent.parent
DATA_PATH = PORTFOLIO_ROOT / "Project_A_Dashboard" / "sample_data" / "mydata_sample.xlsx"
OUT_PATH = SCRIPT_DIR / "analytical_brief.json"


# ----------------------------------------------------------------------------
# Sample-size confidence bands (from methodology Step 4)
# ----------------------------------------------------------------------------
def confidence_band(n_bets: int) -> str:
    if n_bets <= 20:
        return "Low (1-20 bets)"
    if n_bets <= 100:
        return "Early signal (21-100 bets)"
    if n_bets <= 500:
        return "Stronger evidence (101-500 bets)"
    return "Reliable pattern (500+ bets)"


# ----------------------------------------------------------------------------
# Load
# ----------------------------------------------------------------------------
print(f"Loading {DATA_PATH.name}...")
df = pd.read_excel(DATA_PATH, sheet_name="Raw_Data")
df["bet_time"] = pd.to_datetime(df["bet_time"], errors="coerce")
df["bet_date"] = pd.to_datetime(df["bet_date"], errors="coerce").dt.date

# Restrict to a single week for the weekly report context
df = df.sort_values("bet_time").reset_index(drop=True)
week_start = pd.to_datetime(df["bet_time"].min()).date()
week_end = pd.to_datetime(df["bet_time"].max()).date()
print(f"  {len(df):,} bets · {df['bettor'].nunique()} unique wallets · {week_start} → {week_end}")


# ----------------------------------------------------------------------------
# Step 1 — Data quality audit
# ----------------------------------------------------------------------------
expected_fields = [
    "bet_id", "bettor", "bet_time", "sports", "league", "market",
    "usd_amount", "usd_ggr", "odds", "resolved_odds", "subbet_result",
    "bet_type",
]
benchmark_fields_missing = [
    "closing_odds", "pinnacle_odds", "bet365_odds",  # not captured
    "ip_address", "device_id",                       # not captured
    "cashout_offered", "cashout_amount",             # not captured
    "bonus_flag", "bonus_amount",                    # not captured
]
present = [f for f in expected_fields if f in df.columns]
missing = [f for f in expected_fields if f not in df.columns]

bet_status_counts = df["subbet_result"].value_counts().to_dict()


# ----------------------------------------------------------------------------
# Step 2 — KPI Calculation (settled bets only)
# ----------------------------------------------------------------------------
settled_states = {"won", "lost"}
settled = df[df["subbet_result"].isin(settled_states)].copy()

total_bets = len(df)
settled_bets = len(settled)
unique_players = df["bettor"].nunique()
turnover = float(settled["usd_amount"].sum())
company_pl = float(settled["usd_ggr"].sum())
player_pl = -company_pl
hold_pct = (company_pl / turnover * 100) if turnover else 0.0
win_rate = (settled["subbet_result"].eq("won").sum() / settled_bets * 100) if settled_bets else 0.0

# Avg_Won_Odds correctly computed (won bets only, +1 adjustment)
won = settled[settled["subbet_result"] == "won"]
avg_won_odds = float((won["resolved_odds"] + 1.0).mean()) if len(won) else None
avg_stake = float(settled["usd_amount"].mean()) if settled_bets else 0.0


# ----------------------------------------------------------------------------
# Step 4 — Player risk scoring (with explicit sample-size flags)
# ----------------------------------------------------------------------------
player_agg = settled.groupby("bettor").agg(
    bets=("bet_id", "count"),
    stake=("usd_amount", "sum"),
    ggr=("usd_ggr", "sum"),
    wins=("subbet_result", lambda s: (s == "won").sum()),
).reset_index()
player_agg["player_profit"] = -player_agg["ggr"]
player_agg["roi_pct"] = np.where(
    player_agg["stake"] > 0,
    player_agg["player_profit"] / player_agg["stake"] * 100,
    0.0,
)
player_agg["win_rate_pct"] = np.where(
    player_agg["bets"] > 0,
    player_agg["wins"] / player_agg["bets"] * 100,
    0.0,
)
player_agg["confidence"] = player_agg["bets"].apply(confidence_band)

# Top winners — explicit two views to support senior-level discussion
top_winners_overall = player_agg.sort_values("player_profit", ascending=False).head(10)
sharp_candidates = player_agg[
    (player_agg["bets"] <= 20) & (player_agg["player_profit"] > 0)
].sort_values("player_profit", ascending=False)


# ----------------------------------------------------------------------------
# Step 5 — Market risk analysis
# ----------------------------------------------------------------------------
def dim_breakdown(g, dim_name):
    out = g.agg(
        bets=("bet_id", "count"),
        stake=("usd_amount", "sum"),
        ggr=("usd_ggr", "sum"),
        wins=("subbet_result", lambda s: (s == "won").sum()),
    ).reset_index()
    out["hold_pct"] = np.where(out["stake"] > 0, out["ggr"] / out["stake"] * 100, 0.0)
    out["win_rate_pct"] = np.where(out["bets"] > 0, out["wins"] / out["bets"] * 100, 0.0)
    out["confidence"] = out["bets"].apply(confidence_band)
    return out.sort_values("ggr").rename(columns={dim_name: "dimension"})

sport_breakdown = dim_breakdown(settled.groupby("sports"), "sports")
league_breakdown = dim_breakdown(settled.groupby("league"), "league")
market_breakdown = dim_breakdown(settled.groupby("market"), "market")

# Champions League anomaly check (documented finding)
cl = settled[settled["league"] == "Champions League"]
cl_win_rate = (cl["subbet_result"].eq("won").sum() / len(cl) * 100) if len(cl) else 0.0
cl_n = int(len(cl))

# Binomial 95% CI for CL win rate (Wilson)
def wilson_ci(successes, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return (max(0, (centre - half) * 100), min(100, (centre + half) * 100))

cl_wins = int(cl["subbet_result"].eq("won").sum())
cl_ci_low, cl_ci_high = wilson_ci(cl_wins, cl_n)


# ----------------------------------------------------------------------------
# Step 8 — Bot detection (same-second placement)
# ----------------------------------------------------------------------------
ds = df.dropna(subset=["bet_time"]).copy()
ds["sec"] = ds["bet_time"].dt.floor("s")
sec_counts = ds.groupby(["bettor", "sec"]).size()
bot_suspect_accounts = sec_counts[sec_counts > 1].reset_index()["bettor"].unique().tolist()
bot_suspect_n = len(bot_suspect_accounts)

# Behavioral fingerprint candidates — players with same sport-mix + time-of-day pattern
# (Layer-2 lightweight version; full clustering is left to Project B's ML pipeline)
def hour_histogram(sub):
    hours = sub["bet_time"].dt.hour
    return tuple(sub["sports"].value_counts(normalize=True).round(2).to_dict().get(s, 0)
                 for s in sorted(df["sports"].unique())), tuple(hours.value_counts(normalize=True).round(2).to_dict().get(h, 0) for h in range(24))

# Behavioral matches: count players sharing identical (sport_vec, hour_vec) at coarse rounding
buckets = {}
for bettor, sub in df.groupby("bettor"):
    if len(sub) < 5:
        continue
    sv, hv = hour_histogram(sub)
    key = (sv, hv)
    buckets.setdefault(key, []).append(bettor)
behavioral_clusters = [b for b in buckets.values() if len(b) >= 2]
behavioral_match_pairs = sum(len(b) * (len(b) - 1) // 2 for b in behavioral_clusters)


# ----------------------------------------------------------------------------
# Step 10 — Confidence & evidence scoring (rolled up)
# ----------------------------------------------------------------------------
# Each major finding gets an explicit confidence call
findings_confidence = []

findings_confidence.append({
    "finding": "Bot suspects (same-second placement)",
    "metric": f"{bot_suspect_n} accounts",
    "evidence_strength": "Strong" if bot_suspect_n >= 10 else "Moderate",
    "confidence": "High" if bot_suspect_n >= 10 else "Medium",
    "notes": "Direct timestamp signal. Manual review needed before account action.",
})
findings_confidence.append({
    "finding": "Low-volume sharp winners (≤20 bets, profitable)",
    "metric": f"{len(sharp_candidates)} accounts · ${sharp_candidates['player_profit'].sum():,.0f} house loss",
    "evidence_strength": "Weak (small sample per account)",
    "confidence": "Low",
    "notes": "Indistinguishable from variance without CLV data. Recommend monitoring, NOT restriction.",
})
findings_confidence.append({
    "finding": "Champions League player win rate",
    "metric": f"{cl_win_rate:.1f}% ({cl_wins}/{cl_n}, 95% CI: {cl_ci_low:.1f}–{cl_ci_high:.1f}%)",
    "evidence_strength": "Moderate" if cl_n >= 200 else "Weak",
    "confidence": "Medium" if cl_n >= 200 else "Low",
    "notes": ("Anomalous if CI lower bound is above ~55%. "
              "If lower bound includes 50%, treat as variance until larger sample."),
})

football_pl = float(sport_breakdown[sport_breakdown["dimension"] == "Football"]["ggr"].sum())
findings_confidence.append({
    "finding": "Football net house P&L",
    "metric": f"${football_pl:,.0f}",
    "evidence_strength": "Strong" if abs(football_pl) > 2000 else "Moderate",
    "confidence": "High" if abs(football_pl) > 2000 else "Medium",
    "notes": "Largest single sport — trader-side margin lever, not account restriction.",
})


# ----------------------------------------------------------------------------
# Step 12 — Action recommendation skeleton (LLM fills the narrative)
# ----------------------------------------------------------------------------
recommended_actions = []

if bot_suspect_n >= 10:
    recommended_actions.append({
        "priority": "HIGH",
        "category": "Bot mitigation",
        "action": f"Apply velocity-based cooldown to {bot_suspect_n} flagged accounts. Manual review of placement history within 5 business days.",
        "evidence_strength": "Strong",
    })

if abs(football_pl) > 1500:
    recommended_actions.append({
        "priority": "MEDIUM",
        "category": "Market margin",
        "action": "Tiered margin review on Football Full-Time-Result markets (tier-1 leagues +0.5%, tier-2 +1.0%). Avoid uniform increase to preserve volume on liquid leagues.",
        "evidence_strength": "Moderate",
    })

if cl_n >= 200 and cl_ci_low > 55:
    recommended_actions.append({
        "priority": "HIGH",
        "category": "Integrity / pricing",
        "action": "Manual audit of all winning Champions League tickets in observation window. Cross-check settlement timestamps against event end.",
        "evidence_strength": "Moderate (Wilson lower bound exceeds 55%)",
    })
elif cl_n >= 200:
    recommended_actions.append({
        "priority": "MEDIUM",
        "category": "Integrity / monitoring",
        "action": "Continue monitoring Champions League win rate weekly. Do not suspend; CI includes variance scenarios.",
        "evidence_strength": "Weak — sample suggestive but not conclusive",
    })

if len(sharp_candidates) > 0:
    recommended_actions.append({
        "priority": "LOW",
        "category": "Sharp watchlist",
        "action": (f"Add {len(sharp_candidates)} low-volume winning accounts to passive monitoring list. "
                   "Do NOT restrict — sample sizes are insufficient. Re-evaluate at 50 bets."),
        "evidence_strength": "Weak",
    })


# ----------------------------------------------------------------------------
# Assemble the brief
# ----------------------------------------------------------------------------
def df_to_records(d, cols, limit=None):
    sub = d[cols].copy()
    # round floats
    for c in cols:
        if pd.api.types.is_float_dtype(sub[c]):
            sub[c] = sub[c].round(2)
    if limit is not None:
        sub = sub.head(limit)
    return sub.to_dict("records")


brief = {
    "report_metadata": {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "report_type": "Weekly Risk Brief",
        "observation_window": {
            "start": str(week_start),
            "end": str(week_end),
            "days": (week_end - week_start).days + 1,
        },
        "data_source": str(DATA_PATH.relative_to(PORTFOLIO_ROOT)),
        "anonymization": "Wallets mapped to P1..P{n} via sorted deterministic map (see Documentation/methodology.md §7).",
    },
    "data_quality": {
        "fields_present": present,
        "fields_missing_in_source": missing,
        "benchmark_fields_not_captured": benchmark_fields_missing,
        "bet_status_distribution": bet_status_counts,
        "impact_on_analysis": [
            "No CLV calculation possible — Pinnacle/closing odds not captured.",
            "No multi-account linkage via IP/device — relies on behavioral fingerprinting only.",
            "No cashout impact analysis — cashout fields absent.",
            "No bonus abuse detection — promotion flags absent.",
        ],
    },
    "kpi_overview": {
        "total_bets": int(total_bets),
        "settled_bets": int(settled_bets),
        "unique_players": int(unique_players),
        "turnover_usd": round(turnover, 2),
        "company_ggr_usd": round(company_pl, 2),
        "player_pl_usd": round(player_pl, 2),
        "hold_pct": round(hold_pct, 2),
        "player_win_rate_pct": round(win_rate, 2),
        "avg_won_odds": round(avg_won_odds, 2) if avg_won_odds else None,
        "avg_stake_usd": round(avg_stake, 2),
        "interpretation_notes": [
            f"Hold % of {hold_pct:.2f}% is {'below industry-healthy 3-7% range' if hold_pct < 3 else 'within healthy band'}.",
            f"Avg won-odds {avg_won_odds:.2f} computed correctly per methodology §2 (won bets only, +1 adjustment).",
        ],
    },
    "player_risk": {
        "top_winners_overall": df_to_records(
            top_winners_overall,
            ["bettor", "bets", "stake", "player_profit", "roi_pct", "win_rate_pct", "confidence"],
        ),
        "low_volume_sharp_candidates_count": int(len(sharp_candidates)),
        "low_volume_sharp_candidates_total_profit": round(float(sharp_candidates["player_profit"].sum()), 2),
        "low_volume_sharp_candidates_top10": df_to_records(
            sharp_candidates,
            ["bettor", "bets", "stake", "player_profit", "roi_pct", "win_rate_pct", "confidence"],
            limit=10,
        ),
        "sample_size_warning": (
            f"Of {len(sharp_candidates)} flagged 'sharp candidates', "
            f"{int((sharp_candidates['bets'] <= 10).sum())} have ≤10 bets — "
            "indistinguishable from variance without CLV data."
        ),
    },
    "market_risk": {
        "by_sport_top5_losses": df_to_records(
            sport_breakdown.head(5),
            ["dimension", "bets", "stake", "ggr", "hold_pct", "win_rate_pct", "confidence"],
        ),
        "by_league_top5_losses": df_to_records(
            league_breakdown.head(5),
            ["dimension", "bets", "stake", "ggr", "hold_pct", "win_rate_pct", "confidence"],
        ),
        "by_market_top5_losses": df_to_records(
            market_breakdown.head(5),
            ["dimension", "bets", "stake", "ggr", "hold_pct", "win_rate_pct", "confidence"],
        ),
        "champions_league_anomaly": {
            "win_rate_pct": round(cl_win_rate, 2),
            "settled_bets": cl_n,
            "wins": cl_wins,
            "wilson_95ci_pct": [round(cl_ci_low, 2), round(cl_ci_high, 2)],
            "interpretation": (
                "Anomalous if CI lower bound exceeds 55% AND sample > 200. "
                f"Current sample: {cl_n}, CI lower: {cl_ci_low:.1f}% — "
                f"{'meets threshold' if cl_n >= 200 and cl_ci_low > 55 else 'does not meet threshold'}."
            ),
        },
    },
    "behavioral_fingerprinting": {
        "same_second_bot_suspect_accounts": bot_suspect_n,
        "same_second_bot_suspect_ids": bot_suspect_accounts[:30],
        "behavioral_match_pair_count": behavioral_match_pairs,
        "behavioral_cluster_count": len(behavioral_clusters),
        "notes": [
            "Same-second placement: 2+ bets in same one-second window. Strong scripted signal.",
            "Behavioral clusters: shared sport-mix + time-of-day. Statistical signal only; "
            "requires manual review before action.",
        ],
    },
    "confidence_and_evidence": findings_confidence,
    "recommended_actions": recommended_actions,
}


# ----------------------------------------------------------------------------
# Emit
# ----------------------------------------------------------------------------
with open(OUT_PATH, "w") as f:
    json.dump(brief, f, indent=2, default=str)

print(f"\nBrief written to {OUT_PATH.relative_to(PORTFOLIO_ROOT)}")
print(f"  Size: {OUT_PATH.stat().st_size:,} bytes")
print(f"  Top-level sections: {list(brief.keys())}")

# Quick sanity printout
print("\n--- Brief headline numbers ---")
print(f"Settled bets:           {settled_bets:,}")
print(f"Turnover:               ${turnover:,.0f}")
print(f"Company GGR:            ${company_pl:,.0f}")
print(f"Hold %:                 {hold_pct:.2f}%")
print(f"Player win rate:        {win_rate:.2f}%")
print(f"Avg won-odds:           {avg_won_odds:.2f}")
print(f"Bot suspects:           {bot_suspect_n}")
print(f"Low-vol sharp candidates: {len(sharp_candidates)} (${float(sharp_candidates['player_profit'].sum()):,.0f})")
print(f"CL win rate:            {cl_win_rate:.1f}% (CI: {cl_ci_low:.1f}-{cl_ci_high:.1f}%, n={cl_n})")
print(f"Football P&L:           ${football_pl:,.0f}")
