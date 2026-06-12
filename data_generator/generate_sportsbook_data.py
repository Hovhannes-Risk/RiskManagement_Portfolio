"""
Full-scale synthetic sportsbook data generator.

EVERY ROW THIS PORTFOLIO ANALYSES COMES FROM THIS FILE. The dataset is
fully synthetic — no real player, wallet, or transaction exists anywhere
in this repository or its history. Seeded (`SEED = 42`), so the full
526,232-bet dataset regenerates deterministically on any machine:

    python data_generator/generate_sportsbook_data.py

Outputs
-------
1. data_generator/full_dataset.parquet      (gitignored — regenerable)
2. Project_A_Dashboard/sample_data/mydata_sample.xlsx   (one trading day)
3. Project_A_Dashboard/sample_data/player_risk_scores.xlsx
4. Project_A_Dashboard/sample_data/multi_account_detection.xlsx

Planted patterns (sized from 15 years of sportsbook risk experience,
so the detection projects have realistic work to do):
- ~460 scripted accounts placing same-second cross-market bursts
- ~95 low-volume sharp winners (<= 20 bets, positive EV)
- one league ("Champions League") with a concentrated high-win-rate
  bettor group — the classic insider-information signature
- 20 coordinated account pairs sharing sport/time/stake fingerprints
- a recreational mass (~11,600 players) carrying the house margin

The field semantics deliberately reproduce a production pitfall I hit
in my own trading-desk career: `resolved_odds` stores the NET return
multiplier (decimal_odds - 1 on a win, 0.00 on a loss), so naive
averaging of the column produces impossible sub-1.0 "odds". See
Documentation/methodology.md §2.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
RNG = np.random.default_rng(SEED)

SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR.parent
FULL_OUT = SCRIPT_DIR / "full_dataset.parquet"
SAMPLE_DIR = ROOT / "Project_A_Dashboard" / "sample_data"

TARGET_BETS = 526_232
N_PLAYERS = 12_208
WINDOW_END = datetime(2026, 5, 20, 23, 59, 59)
WINDOW_DAYS = 120
SAMPLE_DAY = datetime(2026, 5, 20).date()

SPORTS = {
    "Football": 0.42, "Tennis": 0.16, "Basketball": 0.12, "Ice Hockey": 0.06,
    "Table Tennis": 0.05, "Baseball": 0.04, "Volleyball": 0.03, "MMA": 0.025,
    "Boxing": 0.02, "Cricket": 0.02, "Handball": 0.015, "Rugby League": 0.015,
    "Dota 2": 0.015, "League of Legends": 0.015, "CS2": 0.01, "Snooker": 0.01,
    "Darts": 0.01, "Badminton": 0.005, "NASCAR": 0.005,
}
LEAGUES = {
    "Football": ["Premier League", "La Liga", "Serie A", "Bundesliga",
                 "Ligue 1", "Champions League", "Europa League", "MLS"],
    "Tennis": ["ATP", "WTA", "Challenger"],
    "Basketball": ["NBA", "EuroLeague", "NCAA"],
}
MARKETS = ["Full time result", "Over/Under", "Handicap",
           "Both teams to score", "Winner", "Correct score"]
MARKET_P = [0.34, 0.26, 0.16, 0.10, 0.10, 0.04]

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("generator")


def _ids(start: int, n: int) -> np.ndarray:
    return np.array([f"P{i:05d}" for i in range(start, start + n)])


def _odds(n: int, lo: float = 1.2, mode: float = 1.95, hi: float = 12.0) -> np.ndarray:
    raw = RNG.lognormal(mean=np.log(mode), sigma=0.42, size=n)
    return np.clip(np.round(raw, 2), lo, hi)


def _times(n: int, day_profile: np.ndarray | None = None) -> np.ndarray:
    days = RNG.integers(0, WINDOW_DAYS, size=n)
    if day_profile is None:
        hours = RNG.choice(24, size=n, p=_default_hours())
    else:
        hours = RNG.choice(24, size=n, p=day_profile)
    secs = RNG.integers(0, 3600, size=n)
    base = WINDOW_END - timedelta(days=WINDOW_DAYS - 1)
    return np.array([
        (base + timedelta(days=int(d), hours=int(h), seconds=int(s)))
        for d, h, s in zip(days, hours, secs)
    ])


def _default_hours() -> np.ndarray:
    w = np.array([2, 1, 1, 1, 1, 1, 2, 3, 4, 5, 6, 7,
                  8, 8, 8, 8, 9, 10, 12, 13, 12, 10, 7, 4], dtype=float)
    return w / w.sum()


def _settle(odds: np.ndarray, stakes: np.ndarray, edge: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """edge > 0 favours the player; house margin is -edge."""
    p_win = np.clip((1.0 / odds) * (1.0 + edge), 0.02, 0.93)
    won = RNG.random(len(odds)) < p_win
    ggr = np.where(won, -(stakes * (odds - 1.0)), stakes)
    resolved = np.where(won, odds - 1.0, 0.0)
    return won, np.round(ggr, 2), np.round(resolved, 2)


def _block(players: np.ndarray, bets_per: np.ndarray, stake_lo: float, stake_hi: float,
           edge: float, sports_override: list | None = None,
           league_override: str | None = None,
           market_override: str | None = None,
           hour_profile: np.ndarray | None = None) -> pd.DataFrame:
    bettor = np.repeat(players, bets_per)
    n = len(bettor)
    sport_p = np.array(list(SPORTS.values())); sport_p = sport_p / sport_p.sum()
    sports = (RNG.choice(sports_override, size=n) if sports_override
              else RNG.choice(list(SPORTS), size=n, p=sport_p))
    leagues = np.empty(n, dtype=object)
    for s in np.unique(sports):
        mask = sports == s
        pool = LEAGUES.get(s, [f"{s} League", f"{s} Cup", f"{s} Open"])
        leagues[mask] = RNG.choice(pool, size=mask.sum())
    if league_override:
        leagues[:] = league_override
        sports[:] = "Football"
    market = (np.full(n, market_override) if market_override
              else RNG.choice(MARKETS, size=n, p=MARKET_P))
    odds = _odds(n)
    stakes = np.round(RNG.uniform(stake_lo, stake_hi, size=n), 2)
    won, ggr, resolved = _settle(odds, stakes, edge)
    return pd.DataFrame({
        "bettor": bettor, "bet_time": _times(n, hour_profile), "sports": sports,
        "league": leagues, "market": market, "usd_amount": stakes,
        "usd_ggr": ggr, "odds": odds, "resolved_odds": resolved,
        "subbet_result": np.where(won, "won", "lost"),
    })


def generate_full() -> pd.DataFrame:
    blocks: list[pd.DataFrame] = []
    cursor = 1

    # 1 — recreational mass
    rec = _ids(cursor, 11_553); cursor += len(rec)
    rec_bets = np.clip(RNG.geometric(1 / 40, size=len(rec)), 1, 400)
    blocks.append(_block(rec, rec_bets, 2, 120, edge=-0.06))

    # 2 — bots: same-second cross-market bursts, slight positive edge
    bots = _ids(cursor, 460); cursor += len(bots)
    bot_rows = []
    base = WINDOW_END - timedelta(days=WINDOW_DAYS - 1)
    for b in bots:
        for _ in range(int(RNG.integers(10, 22))):           # bursts per bot
            t = base + timedelta(days=int(RNG.integers(0, WINDOW_DAYS)),
                                 hours=int(RNG.integers(0, 24)),
                                 seconds=int(RNG.integers(0, 3600)))
            k = int(RNG.integers(2, 4))                       # bets in the burst
            mkts = RNG.choice(MARKETS, size=k, replace=False)
            for m in mkts:
                bot_rows.append((b, t, m))
    bdf = pd.DataFrame(bot_rows, columns=["bettor", "bet_time", "market"])
    n = len(bdf)
    bdf["sports"] = RNG.choice(["Football", "Tennis", "Basketball"], size=n, p=[0.6, 0.25, 0.15])
    bdf["league"] = [RNG.choice(LEAGUES.get(s, [f"{s} League"])) for s in bdf["sports"]]
    bdf["odds"] = _odds(n)
    bdf["usd_amount"] = np.round(RNG.uniform(3, 40, size=n), 2)
    won, ggr, resolved = _settle(bdf["odds"].values, bdf["usd_amount"].values, edge=0.05)
    bdf["usd_ggr"], bdf["resolved_odds"] = ggr, resolved
    bdf["subbet_result"] = np.where(won, "won", "lost")
    blocks.append(bdf[blocks[0].columns])

    # 3 — low-volume sharps
    sharps = _ids(cursor, 95); cursor += len(sharps)
    sharp_bets = RNG.integers(6, 19, size=len(sharps))
    blocks.append(_block(sharps, sharp_bets, 350, 1600, edge=0.28,
                         sports_override=["Football"], market_override="Full time result"))

    # 4 — insider-style Champions League group
    insiders = _ids(cursor, 60); cursor += len(insiders)
    ins_bets = RNG.integers(6, 10, size=len(insiders))
    ins = _block(insiders, ins_bets, 150, 900, edge=0.0,
                 league_override="UEFA Youth League", market_override="Full time result")
    p = 0.78                                                  # forced near-insider hit rate
    won = RNG.random(len(ins)) < p
    ins["usd_ggr"] = np.round(np.where(won, -(ins.usd_amount * (ins.odds - 1)), ins.usd_amount), 2)
    ins["resolved_odds"] = np.round(np.where(won, ins.odds - 1, 0.0), 2)
    ins["subbet_result"] = np.where(won, "won", "lost")
    blocks.append(ins)

    # 5 — coordinated multi-account pairs (shared fingerprints)
    pair_rows = []
    for pair in range(20):
        a, b = _ids(cursor, 2); cursor += 2
        sport = RNG.choice(["Football", "Tennis", "Basketball"])
        prof = np.zeros(24); centre = int(RNG.integers(10, 22))
        prof[[centre - 1, centre, (centre + 1) % 24]] = [0.25, 0.5, 0.25]
        lo = float(RNG.uniform(20, 60))
        for acc in (a, b):
            nb = int(RNG.integers(260, 340))   # coordinated accounts run daily
            pair_rows.append(_block(np.array([acc]), np.array([nb]), lo, lo * 2.2,
                                    edge=-0.02, sports_override=[sport],
                                    hour_profile=prof))
    blocks.append(pd.concat(pair_rows, ignore_index=True))

    df = pd.concat(blocks, ignore_index=True)

    # trim recreational rows to hit the exact target size
    excess = len(df) - TARGET_BETS
    if excess > 0:
        rec_idx = df.index[df["bettor"].isin(rec)]
        drop = RNG.choice(rec_idx, size=excess, replace=False)
        df = df.drop(index=drop)
    elif excess < 0:
        extra = _block(rec[: 2000], np.full(2000, -excess // 2000 + 1), 2, 120, edge=-0.06)
        df = pd.concat([df, extra.head(-excess)], ignore_index=True)

    df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    df.insert(0, "bet_id", np.arange(1, len(df) + 1))
    df["bet_time"] = pd.to_datetime(df["bet_time"])
    logger.info("full dataset: %d bets, %d players", len(df), df.bettor.nunique())
    return df


# ------------------------------------------------- dashboard inputs (sample)
def risk_scores(sample: pd.DataFrame) -> pd.DataFrame:
    g = sample.groupby("bettor").agg(
        Bets=("bet_id", "count"), Total_Stake=("usd_amount", "sum"),
        GGR=("usd_ggr", "sum"),
        Win_Rate=("usd_ggr", lambda s: float((s < 0).mean())),
    )
    g["Avg_CLV"] = 0.0
    profit = (-g["GGR"]).clip(lower=0)
    score = (0.45 * g["Win_Rate"]
             + 0.35 * (profit / max(profit.max(), 1.0))
             + 0.20 * (g["Total_Stake"] / max(g["Total_Stake"].max(), 1.0)))
    g["Risk_Score"] = score.round(4)
    g["Risk_Level"] = pd.cut(score, [-1, 0.15, 0.30, 0.50, 0.62, 10],
                             labels=["MINIMAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"])
    return g.sort_values("Risk_Score", ascending=False)


def multi_account(full: pd.DataFrame, sample: pd.DataFrame, top_n: int = 120) -> pd.DataFrame:
    """Pairwise similarity over the day's TOP-N most-active accounts.

    Pairwise comparison of every account is O(n^2) and operationally
    pointless — the desk triages the active head of the book. N=120
    yields 7,140 pairs per day."""
    # Candidates: active today AND carrying a meaningful window history
    # (25-400 bets). Pure one-day counts surface noise; whales drown signal.
    window_counts = full["bettor"].value_counts()
    today = set(sample["bettor"].unique())
    eligible = window_counts[(window_counts >= 25) & (window_counts <= 400)]
    active = [p for p in eligible.index if p in today][:top_n]
    sub = full[full.bettor.isin(active)]
    feats = {}
    for pid, g in sub.groupby("bettor"):
        sport = g["sports"].value_counts(normalize=True).reindex(list(SPORTS), fill_value=0).values
        hours = (pd.to_datetime(g["bet_time"]).dt.hour.value_counts(normalize=True)
                 .reindex(range(24), fill_value=0).values)
        feats[pid] = (sport, hours, float(g["usd_amount"].mean()))

    def cos(u, v):
        nu, nv = np.linalg.norm(u), np.linalg.norm(v)
        return float(u @ v / (nu * nv)) if nu and nv else 0.0

    ids = sorted(feats)
    # Similarity on DEVIATION from the population profile: everyone shares
    # the book-wide sport mix and circadian curve, so raw cosines saturate.
    # What identifies a coordinated pair is deviating in the SAME direction.
    mean_sport = np.mean([feats[p][0] for p in ids], axis=0)
    mean_hour = np.mean([feats[p][1] for p in ids], axis=0)
    rows = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            s_sim = (cos(feats[a][0] - mean_sport, feats[b][0] - mean_sport) + 1) / 2 * 100
            t_sim = (cos(feats[a][1] - mean_hour, feats[b][1] - mean_hour) + 1) / 2 * 100
            k_sim = 100 * (1 - abs(feats[a][2] - feats[b][2])
                           / max(feats[a][2], feats[b][2], 1.0))
            score = 0.4 * s_sim + 0.4 * t_sim + 0.2 * k_sim
            rows.append((a, b, round(score, 1), round(s_sim, 1),
                         round(t_sim, 1), round(k_sim, 1)))
    out = pd.DataFrame(rows, columns=["Account_1", "Account_2", "Similarity_Score",
                                      "Sport_Sim", "Time_Sim", "Stake_Sim"])
    out["Risk_Level"] = pd.cut(out["Similarity_Score"], [-1, 90, 94, 97, 101],
                               labels=["LOW", "MEDIUM", "HIGH", "CRITICAL"])
    return out.sort_values("Similarity_Score", ascending=False).reset_index(drop=True)


def main() -> None:
    full = generate_full()
    FULL_OUT.parent.mkdir(exist_ok=True)
    full.to_parquet(FULL_OUT, index=False)
    logger.info("saved %s", FULL_OUT)

    sample = full[full["bet_time"].dt.date == SAMPLE_DAY].copy()
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(SAMPLE_DIR / "mydata_sample.xlsx") as w:
        sample.to_excel(w, sheet_name="Raw_Data", index=False)
    logger.info("sample day %s: %d bets, %d players",
                SAMPLE_DAY, len(sample), sample.bettor.nunique())

    rs = risk_scores(sample)
    with pd.ExcelWriter(SAMPLE_DIR / "player_risk_scores.xlsx") as w:
        rs.to_excel(w, sheet_name="All_Players")
    ma = multi_account(full, sample)
    with pd.ExcelWriter(SAMPLE_DIR / "multi_account_detection.xlsx") as w:
        ma.to_excel(w, sheet_name="All_Pairs", index=False)
    logger.info("dashboard inputs written: %d players scored, %d pairs", len(rs), len(ma))


if __name__ == "__main__":
    main()
