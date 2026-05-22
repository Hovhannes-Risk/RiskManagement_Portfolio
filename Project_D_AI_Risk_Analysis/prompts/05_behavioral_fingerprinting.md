# Prompt 05 — Behavioural Fingerprinting & Bot Detection

**Role assignment:** Senior AI-Driven Sportsbook Risk Manager.

---

## Input contract

Reads from `analytical_brief.json`:
- `behavioral_fingerprinting.same_second_bot_suspect_accounts`
- `behavioral_fingerprinting.same_second_bot_suspect_ids`
- `behavioral_fingerprinting.behavioral_match_pair_count`
- `behavioral_fingerprinting.behavioral_cluster_count`
- `behavioral_fingerprinting.notes`

Reads from previous step:
- `04.Next Prompt Input Summary` — which markets to cross-reference.

---

## Output contract

1. Behavioural Risk Headline
2. Same-Second Placement (Layer 1 — Direct Bot Signal)
3. Behavioural Clusters (Layer 2 — Cross-Account Pattern Match)
4. Cross-Reference with Market Loss Centres
5. Manual Review Queue
6. Risk Level + Confidence Level (per layer)
7. Recommended Actions
8. Next Prompt Input Summary

---

## The prompt

```text
Act as a Senior AI-Driven Sportsbook Risk Manager.

You are analysing two behavioural signals from the analytical brief
(section: behavioral_fingerprinting):

  Layer 1 — Same-second placement. Accounts placing 2+ bets within the
            same one-second window. This is a strong scripted-behaviour
            signal because manual placement takes 2-4 seconds end-to-end.

  Layer 2 — Behavioural clusters. Accounts sharing identical sport-mix
            and time-of-day patterns. Statistical signal only.

In the operator's full data stack, this prompt would also consume IP,
device-ID, payment-instrument, and registration metadata. None of those
are captured in the portfolio dataset, so this prompt is restricted to
purely behavioural signals. State that limitation in section 1.

Sections to emit (in order, with these exact names):

1. Behavioural Risk Headline
   - One paragraph: the size of each signal.
   - Explicit limitation: "Without IP, device, and payment data, all
     conclusions are behavioural — manual review required before
     account action."

2. Same-Second Placement (Layer 1 — Direct Bot Signal)
   - State count of flagged accounts.
   - State the operational rule: "Two or more placements in the same
     second on the same account is a near-certain scripting signal."
   - List up to 30 flagged IDs (from same_second_bot_suspect_ids).
   - State limitation: "A single false positive is possible from
     multi-bet slip submission. Cross-check by subbet_count per ticket
     before action."

3. Behavioural Clusters (Layer 2 — Cross-Account Pattern Match)
   - State the pair-count and cluster-count from the brief.
   - State the operational rule: "Behavioural fingerprint matches are
     statistical signals, not proof. Treat as manual-review trigger,
     not auto-close trigger." (This is from the methodology — keep
     verbatim.)
   - Do NOT list specific cluster members — at this confidence level,
     surfacing IDs without investigation is reputationally dangerous.

4. Cross-Reference with Market Loss Centres
   - From the previous prompt: which markets are leaking?
   - Are the bot-suspect accounts concentrated in those markets?
     If yes → coherent signal. If no → bot activity is generalised
     scraping, separate from the trader-side loss centres.

5. Manual Review Queue
   - Layer 1 accounts → Priority 1.
   - Layer 2 cluster-member accounts → Priority 2.
   - Total review effort: state account-count and estimated hours
     (15 minutes per Layer 1 account, 30 minutes per Layer 2 cluster).

6. Risk Level + Confidence Level
   - Layer 1: High Risk / High Confidence. (Direct signal.)
   - Layer 2: Medium Risk / Medium Confidence. (Statistical, indirect.)

7. Recommended Actions
   - Layer 1 (bot-strength):
     * Apply velocity-based cooldown (no more than 1 bet per second
       per account on the same market).
     * Force re-authentication on accounts breaching the threshold > N
       times per day.
     * Manual review of placement history.
   - Layer 2 (behavioural):
     * Add cluster members to passive watchlist.
     * Investigation only if combined with another signal (CLV, shared
       payment instrument, etc.) — single-signal action would be unsafe.

8. Next Prompt Input Summary
   - 2 sentences telling the Confidence prompt which findings to grade
     as "Direct evidence" vs "Statistical inference only."

Rules:
- Behavioural fingerprint matches alone do NOT justify account closure.
  This is binding methodology.
- Listing specific cluster-member IDs in a report without case
  investigation creates compliance exposure. Don't.
- Tone: investigative, not accusatory. The phrase "scripted activity"
  is appropriate for Layer 1; "shared behavioural pattern" is the
  right phrase for Layer 2.
```

---

## Why Layer 2 IDs are not listed

In Layer 1 (same-second placement), the signal is direct: the
timestamp is the evidence. Naming the accounts in a report is
defensible.

In Layer 2 (behavioural clustering), the signal is statistical: two
accounts share betting patterns. The most likely explanation is the
same operator, but other explanations exist (two friends with the
same betting strategy, two members of the same tipster service, etc.).
Naming the accounts in a report — before KYC investigation — creates:

- **Compliance exposure** if the named accounts are wrongly profiled.
- **Operational drag** if downstream readers act on the IDs without
  understanding the confidence level.

The senior pattern: surface the **count and cluster size** in the
report; route the **IDs** through a separate investigative workflow.

---

## Failure modes

| Failure | Mitigation |
|---|---|
| LLM lists Layer 2 IDs because the brief contains them | Explicit rule: "Do NOT list specific cluster members" |
| LLM recommends account closure for Layer 2 matches | Binding rule near the top |
| LLM treats Layer 1 and Layer 2 as one signal | Output contract requires separate sections, separate Risk Levels, separate confidence calls |
| LLM forgets the IP/device data is missing | Section 1 requires the limitation to be stated explicitly |

---

## Version history

- **v1** — Single section, IDs from both layers listed. Compliance flagged it.
- **v2** — Split into two layers. Layer 2 IDs removed from report.
- **v3** *(current)* — Added the cross-reference to market loss centres. Behavioural signals only become operationally useful when they correlate with money lost.
