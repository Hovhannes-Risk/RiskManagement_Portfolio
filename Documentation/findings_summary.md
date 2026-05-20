# Findings Summary — Risk Management Portfolio

*Analytical findings from a 526,232-bet dataset across 12,208 wallets,
19 sports, and multiple leagues. Findings are ordered by potential
financial impact and operational urgency.*

---

## Executive summary

Six material risk signals were identified in the dataset. Three of them
together account for the bulk of negative GGR and warrant immediate
operational action; the remaining three are surveillance items that
require manual review before any account action. Total exposure
quantified across the dataset exceeds **$255k in unrecovered house
losses** concentrated in patterns that are consistent with sharp play
and scripted activity rather than recreational betting.

---

## 1. Same-second bot activity

**Signal.** 457 distinct accounts were observed placing two or more bets
within the same one-second window. This is a strong scripted-behaviour
indicator: human reaction time, market selection, stake entry, and
confirmation typically take 2-4 seconds end-to-end even for experienced
bettors.

**Why it matters.** Bots scraping odds and firing on stale prices
extract value directly from the trading book before traders can move the
line. Even when individual stakes are small, aggregate exposure scales
with bot population.

**Recommended action.**
- Apply latency-based velocity limits at the account level (cooldown
  between placements within the same market).
- Force re-authentication or CAPTCHA on accounts that breach the
  one-second threshold more than N times per day.
- Tag the 457 accounts for manual review and trader-team escalation.

---

## 2. Loss concentration in low-volume sharp accounts

**Signal.** Players with 20 or fewer settled bets concentrate
**~$255,000 in cumulative house losses**. This is the inverse of the
expected recreational distribution, where high-frequency low-skill
players typically subsidize the book.

**Why it matters.** This is the classic sharp-player fingerprint —
selective bet placement on +EV opportunities, often around line moves
or off-market prices. The low bet count is not coincidence: it reflects
disciplined bet selection rather than insufficient activity.

**Recommended action.**
- Apply stake limits proportional to detected sharpness (CLV-based
  scoring) rather than to bet count.
- Route these accounts to manual trader approval above defined stake
  thresholds.
- Cross-reference with the multi-account detection output — sharp
  syndicates often operate through wallet rotations.

---

## 3. Champions League win-rate anomaly

**Signal.** Champions League markets exhibit a player-side win rate of
**75.5%**, materially above any plausible market equilibrium. For a
balanced market with a normal house edge, sustained player win rates
above ~55% on a meaningful sample size are not consistent with random
variance.

**Why it matters.** A win rate this high concentrated in a single
competition is consistent with one of three causes: (a) insider
information leakage (lineup news, injury updates, fixed-odds traded
post-event in poorly-policed markets), (b) syndicate activity
exploiting price inefficiencies in pre-match markets, or (c) data
integrity issues in result settlement.

**Recommended action.**
- Manual case review of all winning Champions League tickets in the
  observation window before any account action.
- Audit settlement pipeline for late timestamp issues.
- If (a) is confirmed, tighten pre-match market suspension windows
  around team-news releases.

---

## 4. Football and Premier League as loss centres

**Signal.** Net house P&L breakdown by dimension:

| Dimension | Net house P&L |
|---|---|
| Sport — Football (top loss) | **−$73,400** |
| League — Premier League (top loss) | **−$37,200** |
| Market — "Full time result" (top loss) | **−$82,600** |

**Why it matters.** Football is the deepest market and attracts the
most sharp money; "Full time result" is the most heavily-modelled
market in the industry. A single market line driving more loss than
the worst-performing sport indicates trader-side line management is
the primary lever, not account-side restriction.

**Recommended action.**
- Margin review on Full Time Result pricing for top-tier football
  leagues.
- Compare in-house line vs market consensus on the losing tickets to
  identify systematic mispricing.
- Consider liability caps on Full Time Result markets for matches
  flagged by trading.

---

## 5. Multi-account similarity clusters

**Signal.** Pairwise similarity scoring on sport mix, time pattern, and
stake distribution surfaces multiple **CRITICAL** account pairs with
composite similarity above 90%. The probability of this similarity
arising from independent users is negligible.

**Why it matters.** Multi-accounting is used to circumvent stake limits
and dilute risk signals across "clean" accounts. A CRITICAL pair often
indicates the same operator behind both wallets.

**Recommended action.**
- Apply a unified stake limit across the cluster (treat the pair as one
  exposure unit).
- Investigate KYC overlaps (device fingerprint, payment instrument, IP
  range) before final action.
- Document chain of evidence for compliance.

---

## 6. Odds data integrity (methodology finding)

**Signal.** The `resolved_odds` field in raw data is a **net return
multiplier**, not the decimal odds. A naive average of `resolved_odds`
across all bets understates true odds because losing bets contribute
zero rather than the staked price.

**Why it matters.** Every downstream analytic that uses average odds —
risk scoring, sharp detection, market-quality monitoring — is biased
if this is not corrected. Initial KPI outputs showed average odds below
1.0, which is mathematically impossible for decimal odds and was the
trigger to investigate.

**Resolution.** All average-odds metrics are now computed as
`mean(resolved_odds + 1)` **over won bets only**. Per-sport averages
under the corrected method (Football 2.50, Tennis 2.67, Basketball
2.63, Counter-Strike 2 3.02, Table Tennis 2.98) align with expected
market prices. See `methodology.md` for full derivation.

---

## Prioritisation

| Finding | Impact | Urgency | Effort |
|---|---|---|---|
| Bot activity | High | High | Low (rule-based) |
| Sharp accounts | High | Medium | Medium (CLV scoring) |
| Champions League | Medium | High | High (manual review) |
| Football / FTR markets | High | Medium | Medium (trading-side) |
| Multi-account clusters | Medium | Medium | High (KYC + investigation) |
| Odds methodology fix | N/A (resolved) | N/A | Resolved |

---

## Data and confidentiality

All findings are derived from anonymized data (`P1…P12208`). Raw wallet
addresses and the de-anonymization map are kept private and are not
included in this repository.
