# Project E — Regulated-Market Compliance Layer (Synthetic)

**An MGA/UKGC-world AML + responsible-gambling rules engine, built on
openly synthetic data, with verifiable recall against planted patterns.**

---

## Why this project exists — and why the data is synthetic

Projects A–D run on the synthetic sportsbook dataset. This project
covers the surface they cannot: **regulated-market compliance**. Real
AML cases and responsible-gambling interactions cannot be published in
any form, even anonymized — so this project openly trades realism of
*individuals* for realism of *patterns*. The synthetic generator plants
five behaviour classes at known rates, which buys something a real
dataset can't offer publicly: **the engine's recall is provable.**
`tests/test_compliance.py` asserts ≥80% recall per pattern and ≤5%
false positives on clean players, on every CI run.

This is the honest division of labour: real data where discovery
matters (A–D), synthetic data where publishability is impossible and
verifiability is the point (E).

---

## The five behaviour classes

| Planted pattern | Rule | Severity | Regulated-market mapping |
|---|---|---|---|
| Deposits repeatedly just under the 2,000 EUR EDD threshold within 72h | `AML_STRUCTURING` | CRITICAL | AML threshold-avoidance monitoring → MLRO queue |
| Redeposit within 10 min of a losing bet, stakes escalating | `RG_LOSS_CHASING` | HIGH | Customer-interaction obligation (markers of harm) |
| Rising count and length of 00:00–05:00 sessions | `RG_NIGHT_ESCALATION` | HIGH | Markers of harm — time-of-play |
| Withdrawals cancelled and re-staked | `RG_WITHDRAWAL_REVERSAL` | HIGH | Markers of harm — withdrawal reversal |
| Recreational baseline | — (must NOT alert) | — | Precision guard |

---

## Design principles

1. **The engine never acts on a player.** Every alert routes to a human
   queue (MLRO review, RG team interaction) with a recommended action —
   the same human-gating thesis as Project D's override layer.
2. **Thresholds are configuration, not code.** All triggers live in one
   `CONFIG` dict so a compliance officer can re-tune without touching
   rule logic.
3. **Every rule is a pure, unit-tested function** `frame -> list[Alert]`,
   and every alert carries its evidence, recommended action, and the
   regulatory obligation it maps to.
4. **Conservative severity.** Structuring is the only auto-CRITICAL;
   RG markers start at HIGH/MEDIUM and escalate on persistence, not on
   a single event.

---

## Run it

```bash
python Project_E_Regulated_Compliance/generate_synthetic_data.py   # rebuild data (seeded, deterministic)
python Project_E_Regulated_Compliance/compliance_engine.py         # produce the escalation queue
pytest tests/test_compliance.py -v                                 # prove recall/precision
```

Outputs: `sample_output/escalation_queue.xlsx` — the queue a compliance
desk would triage, sorted CRITICAL → HIGH → MEDIUM.

---

## Files

```
Project_E_Regulated_Compliance/
├── README.md                    This file
├── generate_synthetic_data.py   Seeded generator; plants 4 patterns + clean baseline
├── compliance_engine.py         Typed rules engine -> escalation queue
├── sample_data/                 synthetic_players.xlsx (regenerable)
└── sample_output/               escalation_queue.xlsx
```

## Honest limitations

- Thresholds are illustrative, not jurisdiction-exact; real deployments
  tune them to licence conditions and the operator's risk appetite.
- Affordability checks need income/source-of-funds data that has no
  honest synthetic analogue, so they are intentionally out of scope.
- Pattern realism is stylized; the value demonstrated is the *engine
  architecture and its verifiability*, not the generator.
