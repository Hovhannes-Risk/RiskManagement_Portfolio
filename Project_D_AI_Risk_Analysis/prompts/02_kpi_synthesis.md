# Prompt 02 — KPI Synthesis

**Role assignment:** Senior Sportsbook Risk Analyst.

---

## Input contract

Reads from `analytical_brief.json`:
- `kpi_overview.*`
- `data_quality.bet_status_distribution`

Reads from previous step:
- `01.Next Prompt Input Summary` — tells this prompt which metrics are trustworthy.

---

## Output contract

Sections required:
1. Executive KPI Snapshot (one paragraph)
2. KPI Overview Table
3. Hold % Interpretation
4. Player Win Rate Interpretation
5. Risk Notes (early signals)
6. Confidence Level
7. Next Prompt Input Summary

---

## The prompt

```text
Act as a Senior Sportsbook Risk Analyst.

You are NOT calculating any KPI. The numbers are in the analytical brief
(section: kpi_overview). Your job is INTERPRETATION and EARLY-WARNING
NARRATIVE — to translate numbers into business meaning for the Head of
Risk and Trading Team.

Sections to emit (in order, with these exact names):

1. Executive KPI Snapshot
   - One paragraph. The numbers a manager would scan first.
   - Lead with: total stake, GGR, hold %, settled bets, unique players.

2. KPI Overview Table
   - Reproduce the kpi_overview values as a clean table.
   - Add a "Comment" column with ONE phrase per row (e.g. "below
     industry-healthy band", "consistent with sport mix").
   - Do not invent thresholds — use the interpretation_notes already
     in the brief.

3. Hold % Interpretation
   - Industry-healthy hold for a balanced sportsbook: 3-7%.
   - State whether observed hold is above / within / below this band.
   - State implications: if below, where is the leak likely sitting
     (pricing, sharp dominance, sport mix)? Defer the specific call to
     the Market Risk prompt — your job is the headline only.

4. Player Win Rate Interpretation
   - Compare observed win rate to (1 - average_house_margin).
   - If win rate is above this, players are beating the book on
     aggregate — flag as a downstream investigation item.

5. Risk Notes (early signals)
   - 3-5 bullets, each a SIGNAL not a CONCLUSION.
   - Example phrasing: "Hold % of X is below the 3-7% band. Further
     investigation in Step 04 (player) and Step 05 (market)."

6. Confidence Level
   - All KPIs are deterministic from settled bets. State Very High,
     because they are calculated, not inferred.

7. Next Prompt Input Summary
   - 3 sentences telling the Player Risk prompt which financial
     thresholds matter (e.g., "House lost $X this week — investigate
     concentration at player level").

Rules:
- DO NOT recompute any number.
- DO NOT classify players or markets — that is later prompts' job.
- The brief's interpretation_notes are starting points, not final text.
  Expand them into narrative, but do not contradict them.
- Tone: factual, calm, with one line of "so what?" per metric.
```

---

## Why this prompt does NOT calculate KPIs

A common junior pattern is to put raw bet data in the prompt and ask
the LLM to "calculate the hold %." This fails for three reasons:

1. **Arithmetic hallucination.** LLMs make small arithmetic errors on
   sums and ratios — invisible to a reviewer who trusts the output.
2. **Cost.** Each row in a prompt costs tokens. Bet-level data scales
   poorly; pre-aggregating in Python is free.
3. **Reproducibility.** The same brief produces the same KPIs every
   run. The same prompt against bet-level data may not, depending on
   model variance.

The senior pattern: **Python does arithmetic, LLM does narrative.**

---

## Failure modes

| Failure | Mitigation |
|---|---|
| LLM "rounds" 5.43% to "around 5%" then loses precision in chained reasoning | Output contract requires reproducing kpi_overview values exactly |
| LLM invents an industry benchmark ("healthy hold is 4.7%") | Explicit anchor: "Industry-healthy hold for a balanced sportsbook: 3-7%" |
| LLM jumps to action recommendations | Rule: signals not conclusions in this step |

---

## Version history

- **v1** — Asked LLM to compute hold % from settled bets. 1 in 10 runs returned wrong values.
- **v2** — Pre-computed in Python, LLM only interprets. Determinism restored.
- **v3** *(current)* — Added "Risk Notes (early signals)" — separates the *headline* (this prompt) from the *diagnosis* (later prompts).
