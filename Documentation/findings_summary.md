# Findings Summary — Risk Management Portfolio

*Analytical findings from a fully synthetic 526,232-bet dataset across
12,208 accounts, 19 sports, and a 120-day window. The dataset is
generated deterministically by `data_generator/generate_sportsbook_data.py`
(seed 42) with planted risk patterns sized from 15 years of sportsbook
operations — so every finding below is independently reproducible AND
verifiable against the generator's ground truth. Findings are ordered by
financial impact and operational urgency.*

---

## Executive summary

Five material risk signals were planted in the dataset and recovered by
the detection stack. Total exposure quantified across the window exceeds
**$818k in gross losses to low-volume winning accounts**, with the
single largest concentrated block — **$149.6k — in one low-liquidity
league**, consistent with an insider-information pattern. House hold for
the window is 3.86% on $32.7M turnover ($1.26M GGR).

The point of synthetic ground truth: recall is measurable, not claimed.
The detector stack recovered 77 of 95 planted sharp profiles (the other
18 ended the window unprofitable — variance is part of the design), all
20 planted coordinated pairs, and 100% of scripted accounts.

---

## 1. Same-second bot activity

**Signal.** 464 distinct accounts placed two or more bets inside the
same one-second window, in cross-market bursts. Human placement —
market selection, stake entry, confirmation — takes 2-4 seconds
end-to-end even for experienced bettors.

**Why it matters.** Bots scraping odds and firing on stale prices
extract value before traders can move the line. Individual stakes are
small ($3-40); aggregate exposure scales with bot population.

**Recommended action.**
- Latency-based velocity limits at account level (cooldown between
  placements in the same market).
- Forced re-authentication on accounts breaching the one-second
  threshold more than N times per day.
- Tag flagged accounts for manual review and trader-team escalation.

**Ground truth check.** 460 scripted accounts were planted; the
detector returned 464 (the 4 extras are legitimate coincidental
same-second placements — exactly the false-positive class documented in
methodology.md §10).

---

## 2. Low-volume sharp concentration

**Signal.** 1,814 accounts with ≤20 settled bets ended the window in
profit — gross $818k against the house. Concentration is extreme: the
**top 100 of those accounts carry $517k** of it, with average win rates
far above sustainable recreational variance.

**Why it matters.** The classic sharp signature is not volume — it is
selectivity. A bettor who fires 12 times and wins 9 with $900 average
stakes is exploiting information or pricing, not entertainment.

**Recommended action.**
- Stake-factor review for the top decile of the cohort.
- Bet-level audit of the top 25 accounts: market, timing vs line moves.
- Do NOT mass-limit the long tail — most small profitable accounts are
  ordinary variance (the planted/lucky split below proves it).

**Ground truth check.** 95 sharp profiles were planted with a +25-28%
expected ROI; 77 finished profitable (recall 81%) holding $341k of the
cohort's profit, and 60 of them sit inside the top-100 concentration.
The remaining top-100 slots are recreational accounts that ran hot —
indistinguishable on P&L alone, which is exactly why the
recommendation above audits bet-level behaviour, not outcomes.

---

## 3. UEFA Youth League — insider-pattern win rate

**Signal.** Across 444 settled bets in one low-liquidity league, players
won **344 (77.5%)** — Wilson 95% CI **[73.4%, 81.1%]** — costing the
house **$149.6k**, the worst single league P&L in the book. Exactly 60
accounts produced this volume.

**Why it matters.** Information asymmetry concentrates where liquidity
is thin: youth, reserve, and regional competitions are the classic
venue for insider activity, because pricing is weakest precisely where
participant information is strongest.

**Statistical honesty.** This came out of a scan across dozens of league
cells, so it is exposed to the look-elsewhere effect. Under a
Bonferroni-style correction (z ≈ 3.29 across ~50 cells) the interval
widens to [70.3%, 83.3%] — the lower bound still clears the 55%
operational threshold by 15 points. See methodology.md §9.

**Recommended action.**
- Immediate stake and liability caps on the league, not on accounts.
- Manual audit of the 60 accounts' tickets against team-news timestamps.
- Margin review for all low-liquidity competitions as a class.

---

## 4. Coordinated multi-account pairs

**Signal.** Pairwise behavioural similarity over the active book
surfaced **31 CRITICAL pairs (similarity ≥ 97 on deviation-from-
population fingerprints)** out of 7,140 scanned — sport mix, time-of-day
profile, and stake band aligning simultaneously.

**Why it matters.** Coordinated accounts evade per-account limits,
split arbitrage across identities, and launder bonus abuse.

**Recommended action.** KYC re-verification and shared-infrastructure
checks (device, payment instrument) for CRITICAL pairs; per-cluster
(not per-account) exposure limits.

**Ground truth check.** All 20 planted coordinated pairs scored
99.7-99.9 and rank top of the queue; the additional flagged pairs are
cross-matches between planted clusters sharing a profile — ring
detection working as intended.

---

## 5. Negative-GGR pockets and margin map

**Signal.** Outside the Youth League block, league-level P&L is healthy;
the only other negative pockets are small (NASCAR cells ≈ -$0.4k each).
Hold by market ranges from Over/Under (+$425k) down to Correct score
(+$75k) — no market is net-negative for the window.

**Recommended action.** No structural margin action warranted; keep the
weekly per-league P&L watch with the 500-bet sample-size gate before any
margin move (methodology.md §5-6).

---

## A note on what this dataset is

Every number above is reproducible: run the generator, run the
detectors, get the same findings. None of it involves real players. The
patterns themselves — same-second bursts, low-volume sharps,
thin-league insider concentration, coordinated pairs — are the ones I
spent 15 years catching on live books; the generator encodes that
experience so the detection stack has honest work to do.
