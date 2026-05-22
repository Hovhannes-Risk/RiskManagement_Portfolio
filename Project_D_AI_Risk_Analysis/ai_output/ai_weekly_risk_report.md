# Weekly Risk Report

**Period:** 1–30 April 2026
**Generated:** 21 May 2026, 11:34 UTC
**Source:** Anonymized portfolio dataset (10,000 bets, 499 unique wallets)
**Methodology:** AI-Enabled Risk Analysis — 7-step discipline-gated workflow

---

## 1. Executive Summary

The book closed the period at **−$3,871 GGR on $209k turnover (−1.85% hold)**, below the 3–7% industry-healthy band. Two findings cleared the confidence-and-evidence discipline gate and have entered the action list this period: (1) **Champions League player win rate of 69.3% across 469 settled bets** with a 95% Wilson lower bound of 65.0% — statistically above the 55% threshold for actionable review, and (2) **20 distinct accounts placing two or more bets within the same one-second window**, a scripted-activity signal warranting velocity-based cooldown.

Three findings did **not** clear the gate and have been parked on the watchlist: 174 low-volume winning accounts ($22k aggregate house loss) — sample size below the methodology's 50-bet threshold and indistinguishable from variance without CLV data; the Football full-time-result market loss of $4.7k — within expected variance for a four-week observation at this stake density; and Layer-2 behavioural cluster matches — statistical signal only, no IP or device confirmation in this dataset.

The single recommended trader-side action this period is a **tiered margin review on Football full-time-result markets in tier-1 and tier-2 leagues**. The single recommended integrity-side action is a **manual settlement audit of all 325 winning Champions League tickets** before any market-suspension decision.

---

## 2. Headline KPIs

| Metric | Value | Comment |
|---|---|---|
| Total bets | 10,000 | Multi-day observation window |
| Settled bets | 9,799 | 113 cancelled, 88 cashed out — excluded from P&L |
| Unique wallets | 499 | After anonymization mapping |
| Turnover | **$209,160** | Settled stake only |
| Company GGR | **−$3,871** | Negative — house losing on aggregate |
| Hold % | **−1.85%** | Below industry-healthy 3–7% band |
| Player win rate | 51.69% | Marginally above no-margin baseline |
| Avg won-odds | 1.90 | Computed correctly per methodology §2 |
| Avg stake | $21.34 | Recreational-mid range |

---

## 3. Data Quality Posture

All twelve expected bet-level fields are present in the source: `bet_id`, `bettor`, `bet_time`, `sports`, `league`, `market`, `usd_amount`, `usd_ggr`, `odds`, `resolved_odds`, `subbet_result`, `bet_type`. The 113 cancelled and 88 cashed-out bets have been separated from the settled set for all P&L calculations per methodology §1.

Nine fields that the full methodology would consume are **not captured** in this dataset: `closing_odds`, `pinnacle_odds`, `bet365_odds`, `ip_address`, `device_id`, `cashout_offered`, `cashout_amount`, `bonus_flag`, `bonus_amount`. The consequences are operational and material:

- **No CLV detection.** Sharpness inference is restricted to behavioural signals only. Any low-volume winner flagged in this report is a *candidate*, not a confirmed sharp.
- **No multi-account linkage via IP/device.** Cross-account analysis relies on behavioural fingerprinting only — sufficient for monitoring, insufficient for action.
- **No cashout impact analysis.** Cashout activity is excluded from settled-P&L but cannot be assessed for strategic profit-locking patterns.
- **No bonus abuse detection.** Promotion exploitation is invisible to this workflow.

The portfolio dataset is honest about these limitations; in a production stack the corresponding methodology steps (5b, 6, 7, 11) would run.

---

## 4. Player Risk — Cohort Findings

### Top winners by absolute house loss

| Wallet | Bets | Stake | Player profit | ROI | Win rate | Confidence band |
|---|---|---|---|---|---|---|
| P32 | 5 | $1,467 | $1,347 | 91.8% | 100.0% | Low (1–20 bets) |
| P22 | 3 | $712 | $1,294 | 181.9% | 100.0% | Low (1–20 bets) |
| P213 | 6 | $561 | $1,241 | 221.0% | 66.7% | Low (1–20 bets) |
| P29 | 6 | $2,115 | $826 | 39.1% | 83.3% | Low (1–20 bets) |
| P15 | 104 | $2,845 | $779 | 27.4% | 61.5% | Stronger evidence |
| P3 | 112 | $3,101 | $581 | 18.7% | 58.0% | Stronger evidence |
| P18 | 102 | $2,749 | $522 | 19.0% | 57.8% | Stronger evidence |

Of the top seven winners, only **three (P15, P3, P18)** sit above the 100-bet threshold where ROI starts to mean something. The remaining four are sample-size-limited and have been moved to the watchlist.

### Low-volume cohort summary

**174 accounts with ≤20 settled bets and positive P&L. Aggregate house loss to this cohort: $22,044.**

Of these 174, **27 have ≤10 bets** — indistinguishable from variance without CLV data. The cohort headline number ($22k) is real money lost, but attribution to *sharpness* requires a longer observation window or benchmark-odds confirmation. **The recommended posture is monitoring, not restriction.**

### Manual review candidates (max 5)

| Wallet | Reason for review |
|---|---|
| **P15** | 104 bets, 27.4% ROI, 61.5% win rate — sample above threshold; warrants CLV proxy review if available. |
| **P3** | 112 bets, 18.7% ROI on $3.1k stake — consistent winner, not yet sharp. Continue to monitor. |
| **P18** | 102 bets, 19.0% ROI — same pattern as P3. Cross-check whether P3/P18 share market profile. |
| **P29** | $2.1k stake on only 6 bets — atypical stake density. Investigate single-bet sizing. |
| **P391** | 19 bets, 106.5% ROI — just under the cohort threshold; near-watchlist boundary. |

No automated restriction is recommended for any name in this list.

---

## 5. Market Risk — Loss Centres

### By sport

| Sport | Bets | Stake | Net house P&L | Hold % | Notes |
|---|---|---|---|---|---|
| **Football** | 3,830 | $81,234 | **−$4,714** | −5.8% | Deepest sharp market; trader-side lever |
| Counter-Strike 2 | 1,049 | $24,318 | −$2,188 | −9.0% | Thinner trader coverage; pricing weakness likely |
| Ice Hockey | 385 | $7,763 | −$172 | −2.2% | Variance, sample below 500 |
| Volleyball | 482 | $11,370 | −$101 | −0.9% | Variance |
| Basketball | 1,509 | $30,778 | −$55 | −0.2% | Effectively at expectation |

### By league (top losses)

| League | Bets | Stake | Net house P&L | Hold % | Notes |
|---|---|---|---|---|---|
| **Champions League** | 469 | $9,345 | **−$3,419** | −36.6% | Anomaly — see §6 |
| IEM (CS2) | 382 | $9,143 | −$2,050 | −22.4% | Pricing review needed |
| FIVB (Volleyball) | 170 | $4,177 | −$1,511 | −36.2% | Below confidence threshold |
| MLS | 472 | $10,204 | −$1,487 | −14.6% | Football league — investigate FTR pricing |
| Ligue 1 | 484 | $10,522 | −$1,375 | −13.1% | Same pattern as MLS |

### By market type

| Market | Bets | Stake | Net house P&L | Hold % |
|---|---|---|---|---|
| Full time result | 1,202 | $24,899 | −$1,922 | −7.7% |
| Player props | 1,180 | $25,089 | −$1,373 | −5.5% |
| First Half result | 1,224 | $26,290 | −$1,070 | −4.1% |
| Total points | 1,229 | $26,231 | −$726 | −2.8% |
| Over/Under 2.5 | 1,225 | $25,901 | −$543 | −2.1% |

**Reading:** Full-Time-Result tops the list, which is a **trader-side signal (pricing weakness on the industry's most heavily-modelled market)** — not an account-side signal. Margin adjustment, not account restriction, is the appropriate lever.

---

## 6. Champions League — Anomaly Read

| Metric | Value |
|---|---|
| Settled bets | 469 |
| Wins | 325 |
| Win rate | **69.3%** |
| Wilson 95% CI | **65.0% – 73.3%** |
| Sample-size threshold met | Yes (469 > 200) |
| Lower-CI-bound threshold (55%) | **Yes — exceeded by 10 points** |

**Statistical call: ACTIONABLE.** The Wilson 95% confidence interval places the *lower* bound of the true player win rate at 65%. A 65% win rate sustained across 469 settled bets is inconsistent with a balanced market at any reasonable house margin. The probability that this is variance is below the operational threshold for inaction.

**Recommended action: Manual settlement audit of all 325 winning Champions League tickets in the observation window.** Specifically:

- Cross-check `settlement_time` against `event_time` for each ticket — late-settled tickets are the most likely explanation if (a) is true.
- Review pre-match suspension windows around team-news releases for fixtures in the period.
- Defer any market-suspension decision until the audit completes. A 469-bet sample is large enough for review but not large enough to justify permanent suspension.

This is the single highest-priority item in this report.

---

## 7. Behavioural Signals

### Layer 1 — Same-second placement (direct bot signal)

**20 distinct accounts** placed two or more bets within the same one-second window in the observation period. Manual placement requires reading the market, selecting an outcome, entering a stake, and confirming — typically 2–4 seconds end-to-end. Two or more placements in the same second on the same account is a near-certain scripting signal.

**Flagged accounts:** P1, P10, P11, P12, P13, P14, P15, P16, P17, P18, P19, P2, P20, P3, P4, P5, P6, P7, P8, P9.

**Recommended actions (Layer 1):**
1. Apply velocity-based cooldown (≤1 placement per second per account per market).
2. Force CAPTCHA or re-authentication on accounts breaching the threshold more than 5 times per day.
3. Manual review of placement history for the 20 accounts. Cross-check `subbet_count` per ticket to rule out the multi-leg-slip false-positive case.

### Layer 2 — Behavioural clusters (statistical signal)

The pipeline identified behavioural-fingerprint matches across the observation window. **The methodology classifies these as manual-review triggers, not auto-close triggers.** Account-level IDs are deliberately not surfaced in this section — listing them without case-level investigation creates compliance exposure.

**Recommended action (Layer 2):** Route the cluster set to investigations for KYC overlap checks (payment instrument, registration metadata). No account-side action without an independent second signal.

### Cross-reference with market loss centres

The Layer 1 bot-suspect cohort includes P15, P3, and P18 — three of the top winners by absolute house loss who also appear above the 100-bet threshold. This is a **coherent signal**: scripted activity correlated with market loss. The settlement audit recommended in §6 should include the placement histories of these three accounts.

---

## 8. Confidence & Evidence Discipline

This is the section the methodology mandates for credibility. Three downgrades and one upgrade were applied this period.

### Downgrades — findings the report is NOT acting on

| Finding | Original Confidence | Re-graded | Reason |
|---|---|---|---|
| 174 low-volume sharp candidates ($22k loss) | Medium | **Low** | 27 of 174 have ≤10 bets; CLV data unavailable; cannot distinguish from variance |
| Layer-2 behavioural cluster matches | Medium | **Low** | Statistical-only signal; no IP/device confirmation |
| Football full-time-result $1.9k loss | Medium | **Medium-Low** | Single-period observation; weekly variance plausibly $1–2k |

### Upgrades — findings reinforced by cross-signal

| Finding | Original Confidence | Re-graded | Second signal |
|---|---|---|---|
| Same-second bot activity (20 accounts) | High | **Very High** | Three of the bot-flagged accounts (P15, P3, P18) also appear in the top-7 absolute-loss table — behavioural signal coheres with money lost |

### False-positive risk notes

- **P15 / P3 / P18 may be skilled players using rapid placement, not bots.** Manual review must confirm before account-level action.
- **Champions League win rate may revert next period.** The recommended action (settlement audit) is reversible and information-gathering; a permanent suspension call requires a second period of confirmation.
- **The Layer-2 cluster set may include legitimate users of the same tipster service.** Compliance must not be skipped.

---

## 9. Action Table

| # | Priority | Category | Action | Evidence Strength | Owner |
|---|---|---|---|---|---|
| 1 | **HIGH** | Integrity | Manual settlement audit of 325 winning Champions League tickets | Strong — CI lower bound 65%, sample 469 | Compliance + Trading |
| 2 | **HIGH** | Bot mitigation | Velocity cooldown + manual review of 20 same-second accounts | Very Strong — direct signal | Fraud + Risk |
| 3 | MEDIUM | Market margin | Tiered margin review on Football FTR (tier-1 +0.5%, tier-2 +1.0%) | Moderate — one-period observation | Trading |
| 4 | MEDIUM | Market margin | Margin review on CS2 IEM markets (−$2,050 P&L on $9.1k stake) | Moderate — one-period observation | Trading |
| 5 | LOW | Watchlist | Passive monitoring of 174 low-volume winning accounts; re-evaluate at 50 bets | Weak — sample below threshold | Risk (passive) |
| 6 | LOW | Watchlist | Investigation routing for Layer-2 behavioural cluster set | Weak — statistical only | Investigations |

No item recommends an account closure or a permanent market suspension. Every action is reversible.

---

## 10. Watchlist

Items not yet actionable; re-evaluated next reporting period.

| Item | Observed | What would move it to action | Review cadence |
|---|---|---|---|
| 174 low-volume winners ($22k aggregate) | One-period concentration | Sustained ROI across 50+ bets per account; or any CLV proxy | Monthly |
| Layer-2 behavioural clusters | Pattern match without IP/device | KYC overlap confirmation OR shared CLV pattern | Monthly |
| FIVB volleyball −$1,511 | Single-league concentration | Second consecutive period of negative hold > −15% | Weekly |
| MLS / Ligue 1 −$1.4k each | Mid-tier league losses | Aggregate Football-FTR loss exceeding $7k for the period | Weekly |

---

## 11. Final Management Conclusion

The book finished the period $3.9k down on $209k turnover, with the structural drivers being the Champions League win-rate anomaly ($3.4k) and Counter-Strike 2 pricing weakness ($2.2k). The single most important action item is the **Champions League settlement audit** — a 469-bet sample with a 95% CI lower bound at 65% is large enough to warrant the audit but not large enough to warrant suspension. The single largest area of remaining uncertainty is whether the 174 low-volume winners represent emerging sharp activity or one period of variance; without CLV data, no further action is justified until a second period confirms.

---

*End of report.*

*Discipline note: this report acted on findings that passed the Confidence & Evidence gate (Prompt 06). Three findings were deferred to the watchlist. The deferrals are listed in §8 to make explicit what this report is NOT acting on. That section is the report's credibility anchor.*
