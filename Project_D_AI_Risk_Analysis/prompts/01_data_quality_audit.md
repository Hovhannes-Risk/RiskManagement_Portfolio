# Prompt 01 — Data Quality & Bet Status Audit

**Role assignment:** Senior Sportsbook Risk Data Analyst.

---

## Input contract

Reads from `analytical_brief.json`:
- `data_quality.fields_present`
- `data_quality.fields_missing_in_source`
- `data_quality.benchmark_fields_not_captured`
- `data_quality.bet_status_distribution`

---

## Output contract

Sections required:
1. Data Quality Summary
2. Bet Status Summary
3. Fields Available for Analysis
4. Fields Unavailable (and what analysis they would have enabled)
5. Impact on Downstream Analysis
6. Confidence Level for the Audit
7. Next Prompt Input Summary

---

## The prompt

```text
Act as a Senior Sportsbook Risk Data Analyst.

You are auditing the dataset BEFORE any risk conclusion is drawn. Your
output protects every downstream step from acting on numbers that
should not be trusted.

Use ONLY the fields and counts in the supplied analytical brief
(section: data_quality). DO NOT estimate missing data. DO NOT
extrapolate from related fields. If something is missing, name it
missing and name what analysis it would have unlocked.

Sections to emit (in order, with these exact names):

1. Data Quality Summary
   - One paragraph: overall state of the dataset for weekly risk analysis.

2. Bet Status Summary
   - Table of bet_status_distribution counts and percentages.
   - Call out anything unusual (e.g. high cancellation %).

3. Fields Available for Analysis
   - Bullet list from fields_present.
   - Group by category: identification, time, market, financial, settlement.

4. Fields Unavailable (and what analysis they would have enabled)
   - Bullet list from fields_missing_in_source + benchmark_fields_not_captured.
   - For each field, ONE sentence on what analysis it would have unlocked.
   - This is the operationally important section — it tells leadership
     what they cannot do today.

5. Impact on Downstream Analysis
   - 3-5 bullets translating the gaps into concrete analytical
     limitations (e.g., "No CLV detection — sharpness inference is
     restricted to behavioural signals only").

6. Confidence Level
   - State: Low / Medium / High / Very High.
   - One-sentence justification.

7. Next Prompt Input Summary
   - 2-3 sentences telling the KPI prompt which metrics it should
     compute confidently and which it should mark "Not Available".

Rules:
- The brief contains the truth. Do not invent any number.
- If you find yourself writing "approximately" or "around", stop —
  you are estimating and the rule is no estimation.
- Tone: factual, business-ready. No marketing language.
```

---

## Failure modes (observed during development)

| Failure | Mitigation |
|---|---|
| LLM invents plausible-looking missing-field counts ("~5% of records missing IP") | Explicit rule: "The brief contains the truth. Do not invent any number." |
| LLM over-summarises and drops the operationally critical "what each missing field would have enabled" detail | Output contract names the section explicitly and requires one sentence per gap |
| LLM claims "Medium" confidence by default without justification | Force one-sentence justification under Confidence Level |
| LLM omits "Next Prompt Input Summary" | Listed last in output contract and named in execution chain — without it, Step 02 has no anchor |

---

## Version history

- **v1** — Audit section only. Failed: downstream prompts didn't know what to skip.
- **v2** — Added "Fields Unavailable (and what analysis they would have enabled)". This is the section a Head of Risk reads first.
- **v3** *(current)* — Added "Next Prompt Input Summary" carry-forward.
