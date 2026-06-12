# Prompt 04 — Market Risk Analysis

**Role assignment:** Senior Trading Risk Analyst.

---

## Input contract

Reads from `analytical_brief.json`:
- `market_risk.by_sport_top5_losses`
- `market_risk.by_league_top5_losses`
- `market_risk.by_market_top5_losses`
- `market_risk.champions_league_anomaly`

Reads from previous step:
- `03.Next Prompt Input Summary` — which player cohorts to cross-reference.

---

## Output contract

1. Market Risk Headline
2. Loss Centres — by Sport
3. Loss Centres — by League
4. Loss Centres — by Market Type
5. UEFA Youth League Anomaly — Statistical Read
6. Risk Level + Confidence Level (per dimension)
7. Recommended Actions (trader-side, not account-side)
8. Next Prompt Input Summary

---

## The prompt

```text
Act as a Senior Trading Risk Analyst.

You are analysing where house P&L LEAKED across structural dimensions
this week (sport, league, market type). The brief contains pre-computed
top-5 loss centres per dimension (section: market_risk).

Sections to emit (in order, with these exact names):

1. Market Risk Headline
   - One paragraph: the structural shape of loss this week.
   - Identify the single biggest dimensional driver (sport or league
     or market type) and quantify in dollars.

2. Loss Centres — by Sport
   - Reproduce by_sport_top5_losses as a table.
   - For each row, ONE phrase in a Notes column: "deep sharp market",
     "low liquidity — high variance", "thin trader coverage", etc.

3. Loss Centres — by League
   - Reproduce by_league_top5_losses as a table.
   - Pay particular attention to UEFA Youth League if it appears —
     defer the anomaly analysis to section 5.

4. Loss Centres — by Market Type
   - Reproduce by_market_top5_losses as a table.
   - "Full time result" is the most heavily-modelled market in the
     industry. If it tops the list, that is a TRADER-side signal
     (pricing weakness) not an ACCOUNT-side signal (sharp behaviour).

5. UEFA Youth League Anomaly — Statistical Read
   - Reproduce champions_league_anomaly verbatim.
   - State the interpretation rule the brief provides.
   - Compute (verbally — no arithmetic): does the Wilson 95% CI lower
     bound exceed 55%?
       * If YES and sample > 200 → flag as ACTIONABLE anomaly.
       * If NO or sample ≤ 200  → flag as MONITORING anomaly only.
   - This is the ONLY place the LLM is allowed to draw a statistical
     conclusion, and only because the CI thresholds are explicit.

6. Risk Level + Confidence Level
   - Per dimension. Sports typically Medium Risk / Medium-High Confidence.
   - UEFA Youth League: depends on CI test result above.

7. Recommended Actions (trader-side, not account-side)
   - For loss-centre markets: margin review, line management,
     liability caps — NOT account restrictions.
   - For UEFA Youth League: manual settlement audit if actionable,
     continued monitoring if not.
   - Frame all actions as REVERSIBLE (start narrow, expand if signal
     persists) — irreversible actions like permanent market suspension
     require a longer observation window.

8. Next Prompt Input Summary
   - 2 sentences summarising the dimensions that need cross-reference
     with the behavioural fingerprinting cohort (next prompt).

Rules:
- The methodology states: trader-side line management is the primary
  lever for market-level loss centres. Account restrictions targeting
  the players who bet those markets are a SECONDARY lever and only
  appropriate when player-level evidence is independent.
- A single week is RARELY enough for permanent action on a market.
  Monthly trend is the right horizon for that decision.
- Tone: surgical. Each recommendation is a specific market or league,
  not a sport-wide blanket statement.
```

---

## Why trader-side vs account-side matters here

A junior risk analyst seeing $4,700 lost on Football this week
recommends "restrict the players who won on Football."

A senior risk analyst sees the same number and recommends "review
margins on Full-Time-Result markets in the leagues where the loss
concentrated."

The first is account-side (punitive, hurts retention, addresses the
symptom). The second is trader-side (preserves the player base,
addresses the cause). Both produce the same P&L improvement if the
margin call is right.

The UEFA Youth League case is the exception: a sustained 73%+ win rate
across 444 settled bets is unlikely to be a margin problem and
warrants integrity-side action (settlement audit, news-window review).

---

## Failure modes

| Failure | Mitigation |
|---|---|
| LLM recommends "ban UEFA Youth League players" | Rule: "Recommended Actions (trader-side, not account-side)" |
| LLM treats UEFA Youth League and Football identically as "loss centres" | Section 5 separates UEFA Youth League into a statistical read |
| LLM recommends permanent market suspension from one week of data | Rule: "Frame all actions as REVERSIBLE" |
| LLM extrapolates the weekly number to monthly with arithmetic | Rule: "no arithmetic" — the brief already contains the per-period number |

---

## Version history

- **v1** — Combined all dimensions into one table. Lost the trader-vs-account distinction.
- **v2** — Separated UEFA Youth League into its own section with the CI test.
- **v3** *(current)* — Added the explicit "trader-side, not account-side" rule for the action section. This single addition cut recommended account restrictions from ~10/week to ~1/week.
