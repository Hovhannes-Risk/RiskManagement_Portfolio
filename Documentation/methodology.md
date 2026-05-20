# Methodology — Risk Management Portfolio

*Technical methodology behind the analytical work in this portfolio.
Covers data cleaning, the odds-field discovery, detection logic for
bots and multi-accounts, risk scoring, and reporting.*

---

## 1. Dataset

- **526,232** settled bets
- **12,208** unique wallets
- **19** sports
- Per-bet fields used: `bettor`, `bet_time`, `usd_amount`, `usd_ggr`,
  `sports`, `league`, `market`, `resolved_odds`, `subbet_result`
- All wallet identifiers anonymized to `P1…P12208` via a sorted,
  deterministic map (`bettor_mapping_PRIVATE.xlsx`, kept outside the
  repository).

---

## 2. The `resolved_odds` discovery

### Symptom

Initial KPI generation produced an `Avg_Odds` column with values below
1.0 (a representative row: `Avg_Odds = 0.71`). Decimal odds cannot be
below 1.0 by definition — the stake itself is always returned on a
winning bet, so the multiplier is bounded by 1.

### Investigation

Inspection of raw bet rows showed:

| `subbet_result` | `resolved_odds` value |
|---|---|
| `won` | `decimal_odds − 1` |
| `lost` | `0.00` |
| `cancelled` | varies |
| `cashout` | partial payout multiplier |

All 237,602 lost bets in the dataset carried `resolved_odds = 0`,
confirming the field is the **net return multiplier** (profit per unit
stake), not the decimal odds.

### Why the naive average broke

The original logic averaged `resolved_odds` across every bet a player
placed. Losing bets contributed zeros and dragged the average toward
zero, producing values like 0.71 that were mathematically impossible
for any odds metric.

### Worked example — player P3

| Field | Value |
|---|---|
| Total bets | 7 |
| Won bets | 4 |
| Sum of `resolved_odds` | 4.97 (only winning bets are non-zero) |
| Naive Avg_Odds | 4.97 / 7 = 0.71 |
| Correct Avg_Won_Odds | 4.97 / 4 + 1 = **2.24** |

A simple `+1` adjustment would have given 1.71, also wrong. The fix
requires both isolating winning bets and adding 1.

### Corrected formula

```
Avg_Won_Odds = mean(resolved_odds + 1)   over won bets only
```

Per-sport averages under the corrected method:

| Sport | Avg won odds |
|---|---|
| Football | 2.50 |
| Tennis | 2.67 |
| Basketball | 2.63 |
| Counter-Strike 2 | 3.02 |
| Table Tennis | 2.98 |

These align with realistic mid-market prices for each sport.

### Handling players who never won

Players with zero winning bets have no decimal-odds sample. These cells
are left blank rather than imputed to avoid biasing downstream
aggregations.

---

## 3. Bot detection — same-second placement

### Logic

A bot is operationally defined as an account that placed two or more
bets within the same one-second window. Implementation:

```python
df["sec"] = df["bet_datetime"].dt.floor("s")
counts = df.groupby(["bettor", "sec"]).size()
bot_suspects = counts[counts > 1].reset_index()["bettor"].nunique()
```

### Why this works

Manual placement requires reading the market, selecting the outcome,
entering a stake, and confirming. Even an experienced bettor on a
familiar platform rarely completes this in under two seconds. Two or
more placements in the same second on the same account is a
near-certain scripting signal.

### Known limitations

- A single false positive is possible from multi-bet slip submission
  (multiple selections confirmed in one click). Mitigation: cross-check
  by `subbet_count` per ticket before action.
- Distributed bots that rate-limit themselves to ≤1 placement/second
  will not be caught by this rule alone. A second-layer detector is
  needed for those (out of scope for this portfolio).

### Result

457 distinct accounts flagged. The flag is a *surveillance signal*,
not an automatic action — manual review is required before any account
restriction.

---

## 4. Multi-account similarity

### Approach

Each candidate account pair is scored on three dimensions, then
combined into a composite similarity score:

| Component | What it measures |
|---|---|
| **Sport similarity** | Cosine similarity of normalized sport-mix vectors |
| **Time similarity** | Overlap of betting-time histograms (hour-of-day) |
| **Stake similarity** | Distribution similarity of stake amounts |

The composite score is bounded 0-100. Pairs above 90 are flagged as
CRITICAL.

### Why these three

Operators running multiple accounts almost always inherit their own
preferences across wallets: the sports they understand, the hours they
trade, and the stake sizes their bankroll supports. Two of the three
matching is suggestive; all three matching at high similarity is
strongly indicative.

### Action gate

Similarity alone does not prove multi-accounting. Recommended workflow
before action:
1. Pull KYC records for both accounts
2. Compare device fingerprint, IP range, payment instrument
3. Escalate to compliance with the chain of evidence

---

## 5. Player risk scoring

### Feature set

| Feature | Rationale |
|---|---|
| Bet count | Volume signal |
| Total stake | Exposure signal |
| Net GGR | Direct house-side outcome |
| Average winning odds | Market preference / sharpness proxy |
| Win rate | Recent performance |
| CLV proxy | Sharpness (if available) |

### Output

A normalized score on a **0-1 scale** mapped to discrete bands:

| Score range | Band |
|---|---|
| ≥ 0.70 | CRITICAL |
| 0.50 - 0.69 | HIGH |
| 0.30 - 0.49 | MEDIUM |
| 0.15 - 0.29 | LOW |
| < 0.15 | MINIMAL |

### Known limitation

The model shows weak discrimination at the low-volume tail — a large
number of accounts cluster at exactly the baseline score (~0.2). This
is expected: with only a handful of bets, there is insufficient signal
to differentiate accounts. The dashboard's low-volume sharp-player flag
is the complementary check for this tail.

---

## 6. Reporting

### Stack

`matplotlib` with `PdfPages` for multi-page output. Layout uses manual
`fig.add_axes([x, y, w, h])` placement (0–1 figure-relative coordinates)
rather than the grid system to keep cards, headers, and tables on a
deterministic grid across runs.

### Why matplotlib instead of a templating tool

- Zero external dependencies beyond what the analytical pipeline
  already uses.
- Full control over every pixel — KPI cards, navy header band, table
  cell widths.
- Deterministic output for diffing reports week-over-week.

### Outputs

| Report | Cadence | Audience |
|---|---|---|
| Daily Risk Report | Daily | Risk desk |
| Weekly Executive Summary | Weekly | Management |

Both reports read from the same anonymized analysis files used by
the Streamlit dashboard, so the anonymization step happens once
upstream and every output downstream is consistent.

---

## 7. Anonymization

### Why

The full raw dataset contains identifiable wallet addresses. Any work
intended for portfolio publication, external review, or sharing
requires substitution.

### How

A master mapping `{wallet: P-id}` is built **once** from the full
dataset:

```python
wallets = sorted(set(raw["bettor"]))
mapping = {w: f"P{i}" for i, w in enumerate(wallets, 1)}
```

The `sorted` step is essential — it makes the assignment deterministic
across runs. Without it, the same wallet would be assigned different
P-ids in different sessions, breaking cross-file consistency.

### Operational rule

Report scripts **load** the master mapping, they never rebuild it.
Rebuilding from a subset of players (e.g. one day's data) would assign
different IDs depending on who appeared in that subset.

The mapping file is kept private and is not part of this repository.

---

## 8. Limitations and assumptions

- **Time zone.** All timestamps are treated as a single zone; if the
  source system writes in operator-local time, late-night placements
  may be misclassified as same-second activity around DST boundaries.
- **Cashouts.** Treated as a separate settlement state. Their
  `resolved_odds` values are not used in the average-odds computation.
- **Cancellations.** Excluded from all P&L and odds calculations.
- **Test accounts.** Not separately flagged; if internal QA wallets
  appear in the data, they will show as low-volume outliers.

---

## References

- `Project_A_Dashboard/risk_dashboard.py` — Streamlit implementation
- `Project_B_ML_Anomaly_Detection/` — scoring and detection scripts
- `Project_C_Automated_Reports/` — PDF report generators
- `anonymize.py` — shared anonymization module
