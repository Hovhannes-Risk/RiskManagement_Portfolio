# Prompt 03 — Player Risk Scoring

**Role assignment:** Senior AI-Driven Sportsbook Risk Manager.

---

## Input contract

Reads from `analytical_brief.json`:
- `player_risk.top_winners_overall`
- `player_risk.low_volume_sharp_candidates_count`
- `player_risk.low_volume_sharp_candidates_total_profit`
- `player_risk.low_volume_sharp_candidates_top10`
- `player_risk.sample_size_warning`

Reads from previous step:
- `02.Next Prompt Input Summary`

---

## Output contract

1. Player Risk Headline
2. Top Winners Table (top 10 overall)
3. Low-Volume Winners Analysis (sharp-candidate cohort)
4. Sample-Size Discipline Note
5. Manual Review Candidates
6. Risk Level + Confidence Level (per cohort, not blanket)
7. Recommended Actions
8. Next Prompt Input Summary

---

## The prompt

```text
Act as a Senior AI-Driven Sportsbook Risk Manager.

You are analysing two PLAYER cohorts from the analytical brief
(section: player_risk):

  (a) Top 10 winners by absolute house-loss contribution (any sample size).
  (b) Low-volume winning cohort (≤20 settled bets, profitable).

Cohort (a) tells you where the money LEAKED this week.
Cohort (b) tells you where SHARPNESS may be HIDING (small sample, but
the inverse of the expected recreational distribution).

Sections to emit (in order, with these exact names):

1. Player Risk Headline
   - One paragraph: what the player population looks like this week.
   - Lead with the dollar number from cohort (b)'s total profit —
     this is the senior-relevant figure.

2. Top Winners Table
   - Reproduce top_winners_overall verbatim as a table.
   - Columns: bettor, bets, stake, player_profit, roi_pct,
     win_rate_pct, confidence.
   - Add a "Notes" column with ONE phrase per row (e.g. "high volume,
     low edge — recreational", "small sample, defer judgment").

3. Low-Volume Winners Analysis
   - State the cohort size and aggregate house loss to this cohort.
   - Reproduce top 10 of the cohort as a table.
   - Critical: DO NOT call this cohort "sharp" without qualification.
     The methodology calls them sharp CANDIDATES because sample size
     is below the 50-bet threshold for any confident classification.

4. Sample-Size Discipline Note
   - Reproduce the sample_size_warning from the brief verbatim, then
     add ONE sentence explaining why this matters for downstream action.

5. Manual Review Candidates
   - List up to 5 specific bettors who deserve human review.
   - For each: 1-line reason (e.g., "P124 — 8 bets, 75% win rate,
     $890 profit. Sample too small for restriction, large enough to
     watch.").

6. Risk Level + Confidence Level
   - Cohort (a) — top winners: Risk Level, Confidence Level.
   - Cohort (b) — low-volume winners: Risk Level, Confidence Level.
   - These will typically diverge. Cohort (a) is High Risk / High
     Confidence (real money lost). Cohort (b) is Medium Risk / Low
     Confidence (suggestive but unproven).

7. Recommended Actions
   - For cohort (a): tier-1 monitoring, no immediate restriction
     unless individual sample > 100 bets AND ROI > 5%.
   - For cohort (b): passive watchlist, re-evaluate at 50 bets.
   - Do NOT recommend account closures or hard limits based on this
     week's data alone.

8. Next Prompt Input Summary
   - 2 sentences telling the Market Risk prompt which player cohort
     is leaking the most money — to cross-reference with sport/market
     concentration.

Rules:
- The methodology states: do not classify a player as Sharp/Professional
  based on win rate or ROI alone when sample size is below ~50 bets.
  This rule is binding.
- The methodology states: positive CLV and repeated value are stronger
  than short-term profit. CLV is unavailable in this dataset — call
  this gap out explicitly when discussing cohort (b).
- Tone: cautious, evidence-graded. The senior signal here is
  RESTRAINT, not aggressive flagging.
```

---

## Why "RESTRAINT" is the senior signal

Junior risk analysts flag everyone who beats the book this week.
Senior risk analysts know that:

- A player with 8 bets and a 75% win rate is **variance** until proven
  otherwise.
- Restricting recreational winners hurts retention and brand.
- The cost of a false positive (limiting a recreational player who
  got lucky for one week) is **higher** than the cost of a false
  negative (letting a real sharp run for one more week) — at small
  sample sizes.

This prompt is structured to embed that asymmetry into the LLM's
output.

---

## Failure modes

| Failure | Mitigation |
|---|---|
| LLM labels every winner as "Sharp" | Explicit binding rule referencing the 50-bet threshold |
| LLM recommends account closures from one week of data | Rule: "Do NOT recommend account closures or hard limits based on this week's data alone" |
| LLM ignores the sample-size warning | Output contract requires verbatim reproduction of sample_size_warning |
| LLM produces a single blanket Risk Level for "all players" | Output contract requires separate Risk/Confidence calls per cohort |

---

## Version history

- **v1** — Asked LLM to score every player. Output was 500 rows of identical-looking risk scores. Useless.
- **v2** — Pre-aggregated to two cohorts in Python. LLM interprets cohorts, not individuals.
- **v3** *(current)* — Added the asymmetry note. The LLM was still defaulting to "restrict" for small-sample winners; the binding rule and the cohort-level Risk Level requirement fixed it.
