# KWST v5.2 Dry-Run Report — null-price tour re-extraction

**Generated:** 2026-05-03T18:31:53.563Z
**Branch:** `feat/kwst-v52-price-extraction`
**Mode:** `--dry-run-only` (no writes to tours-data.json)

## 1. Inputs

- KWST total tours: 1010
- Tours with `price: null` evaluated: **428**
- Extractor: v5.4 baseline + v5.2 dominant-price gate (ported verbatim from wanderusvi)
- Page fetch: Playwright (chromium headless), 1.5 s settle wait

## 2. Result distribution

| Outcome | Count | Disposition |
|---|---:|---|
| **high** (v5.4 Method 1/2 — adult/per-person anchor) | 5 | "From $X" if applied |
| **medium** (v5.4 native — Method 3/4/6) | 48 | "From $X" if applied |
| **medium** (v5.2 dominant-price gate) | 41 | "From $X" if applied |
| **low** (Method 5 unanchored, gate FAILed) | 12 | stays "Check availability" |
| **no-price** (extractor returned null) | 322 | stays "Check availability" |
| **error** (fetch/parse) | 0 | stays "Check availability" |
| **Total** | 428 | |

**Net effect if applied --live:** 94 tours flip from "Check availability" → "From $X" (22.0% of the 428). 334 stay hidden.

## 3. Cat-E candidate sanity check

**0 Cat-E candidates** detected among gate PASSes. Disqualifier blocklist (`additional, extra, option, optional, rental, nitrox, upgrade, supplement, add-on, addon, surcharge` + `+$` literal) appears to be holding.

## 4. Sample 10 promoted tours

### 550482 — Sunday Funday Swim & Brunch

- company: Hindu Charters LLC - Argo Navis
- extracted price: **$135** (medium, unknown)
- priceSource: `v52-dominant-gate`
- gate distinct $-values: [75,135]
- gate matched token: `$135`
- gate ±40 char window:

  ```
   Free cancellation Instant confirmation $135 Over 21 $135 Under 21 Ages 12 - 20 $75 
  ```
- all $-hits in page: ["$135","$135","$75"]

### 550483 — Key West Pride Brunch Sail & Swim

- company: Hindu Charters LLC - Argo Navis
- extracted price: **$135** (medium, unknown)
- priceSource: `v52-dominant-gate`
- gate distinct $-values: [135]
- gate matched token: `$135`
- gate ±40 char window:

  ```
   West Pride • 3 Hours • Cozzie Contest! $135 Over 21 Prices for Friday, June 5, 2026
  ```
- all $-hits in page: ["$135"]

### 431194 — The Dry Tortugas

- company: Laid Back Key West
- extracted price: **$2900** (medium, unknown)
- priceSource: `v52-dominant-gate`
- gate distinct $-values: [2900]
- gate matched token: `$2,900`
- gate ±40 char window:

  ```
  s • A day on the water ! Fuel Included! $2,900 Ten Hour Charter Prices for Thursday, M
  ```
- all $-hits in page: ["$2,900"]

### 622772 — 6 Hour Private Fishing Charter

- company: 3rd Degree Charters
- extracted price: **$1050** (medium, unknown)
- priceSource: `v52-dominant-gate`
- gate distinct $-values: [1050]
- gate matched token: `$1,050`
- gate ±40 char window:

  ```
  ate Fishing Charter for up to 4 people! $1,050 Six Hour Private Fishing Charter Price 
  ```
- all $-hits in page: ["$1,050"]

### 622770 — 8 Hour Private Fishing Charter

- company: 3rd Degree Charters
- extracted price: **$1200** (medium, unknown)
- priceSource: `v52-dominant-gate`
- gate distinct $-values: [1200]
- gate matched token: `$1,200`
- gate ±40 char window:

  ```
  people • Our most popular fishing trip! $1,200 Eight Hour Private Fishing Charter Pric
  ```
- all $-hits in page: ["$1,200"]

### 643117 — Full Day Snorkel & Sandbar Charter

- company: The Happy Captain
- extracted price: **$1200** (medium, unknown)
- priceSource: `v52-dominant-gate`
- gate distinct $-values: [1200]
- gate matched token: `$1,200`
- gate ±40 char window:

  ```
   the Happy Captain’s Glass-Bottom Boat! $1,200 Charters Prices for Tuesday, May 5, 202
  ```
- all $-hits in page: ["$1,200"]

### 328392 — 4 Hour Fishing Trip

- company: Pirate Adventure Charters
- extracted price: **$749** (medium, unknown)
- priceSource: `v52-dominant-gate`
- gate distinct $-values: [749]
- gate matched token: `$749`
- gate ±40 char window:

  ```
  r Fishing Trip 4 Hours • Up to 6 People $749 Private charters Up to 6 people Prices 
  ```
- all $-hits in page: ["$749"]

### 328393 — 6 Hour Fishing Trip

- company: Pirate Adventure Charters
- extracted price: **$949** (medium, unknown)
- priceSource: `v52-dominant-gate`
- gate distinct $-values: [949]
- gate matched token: `$949`
- gate ±40 char window:

  ```
  r Fishing Trip 6 Hours • Up to 6 people $949 Private charters Up to 6 people Prices 
  ```
- all $-hits in page: ["$949"]

### 513692 — 6 Hour Offshore Fishing Charter

- company: Wall to Wall Fishing Charters
- extracted price: **$1400** (medium, unknown)
- priceSource: `v52-dominant-gate`
- gate distinct $-values: [1400]
- gate matched token: `$1,400`
- gate ±40 char window:

  ```
  ishing Charter 6 Hours • Up to 6 Guests $1,400 Private Charters Captain Included • Up 
  ```
- all $-hits in page: ["$1,400"]

### 513694 — Near Dry Tortugas Fishing Charter

- company: Wall to Wall Fishing Charters
- extracted price: **$2000** (medium, unknown)
- priceSource: `v52-dominant-gate`
- gate distinct $-values: [2000]
- gate matched token: `$2,000`
- gate ±40 char window:

  ```
  ishing Charter 8 Hours • Up to 4 Guests $2,000 Private Charters Captain Included • Up 
  ```
- all $-hits in page: ["$2,000"]

## 5. Sample 5 stays-hidden tours

### 415838 — Offshore Fishing Charters

- outcome: low
- gate criterion failed: 2
- distinct $-values: [1199,1399,1599]
- all $-hits: ["$1,199","$1,399","$1,599"]

### 571027 — Sandbar, Hidden Beaches and Island Adventuring

- outcome: low
- gate criterion failed: 2
- distinct $-values: [297,396,495,594,693,792]
- all $-hits: ["$297","$396","$495","$594","$693","$792"]

### 571024 — Snorkeling

- outcome: low
- gate criterion failed: 2
- distinct $-values: [447,596,745,894,1043,1192]
- all $-hits: ["$447","$596","$745","$894","$1,043","$1,192"]

### 571032 — Offshore Fishing

- outcome: low
- gate criterion failed: 2
- distinct $-values: [597,796,995,1194,1393,1592]
- all $-hits: ["$597","$796","$995","$1,194","$1,393","$1,592"]

### 571039 — Marquesas Keys Island Wreck Hop with Snorkel Gear

- outcome: low
- gate criterion failed: 2
- distinct $-values: [995,1194,1393,1592]
- all $-hits: ["$995","$1,194","$1,393","$1,592"]

## 6. No-price decomposition (322 / 428 tours)

The extractor returned `null` on 75% of targets. Decomposing the 322:

| Sub-bucket | Count | What it means |
|---|---:|---|
| Page contains no `$N` at all | **286** (89% of no-price) | Genuinely no public price — booking-flow gated, page didn't render the price section, or 3rd-party operator that doesn't surface FareHarbor's standard pricing markup. No remediation via extractor improvements. |
| Page has `$N` but all 6 v5.4 methods returned null | **36** (11% of no-price) | Recoverable in a future extractor revision. Examples: 353562 (`$595, $20` on page — no anchor verb, only 2 distinct values so calendar Method 6 misses; could pass a future relaxed gate), 439802 (`$0` only — junk), 627703 (`$1,100` single value — no anchor, no calendar repetition). |

**Implication:** the practical ceiling for KWST gate-driven graduation is **~94 + 36 = ~130** of 428 (~30%) without bigger extractor changes. The remaining ~286 require a different remediation path (manual price entry, operator outreach, alternate scraping target).

## 7. Comparison vs. USVI v5.2 baseline

| Metric | USVI (156 lows) | KWST (428 nulls) |
|---|---:|---:|
| Targets evaluated | 156 | 428 |
| v5.4 native promotions (high+medium) | n/a (started from low) | 53 |
| v5.2 gate promotions (low → medium) | 77 | 41 |
| Net promoted | 77 (49%) | 94 (22%) |
| Stayed hidden | 79 (51%) | 334 (78%) |
| Cat-E policy violations | **0** ✓ | **0** ✓ |

KWST's lower promotion rate reflects that the audit selected USVI's low-confidence subset (already-extracted prices needing graduation), while KWST's targets are pure null-price tours where the extractor either fails to find a price at all (322) or finds one in a multi-tier shape the gate blocks (12).

## 8. Out of scope for this run

- No edits to `tours-data.json`.
- No commits, no push, no deploy.
- `--live` mode not implemented yet — adopt USVI's `apply-v52-live.js` pattern when ready.
