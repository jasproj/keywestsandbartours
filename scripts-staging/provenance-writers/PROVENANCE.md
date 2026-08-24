# Price-provenance writers rescued from /tmp

Rescued 2026-08-24 (s44) ahead of the /tmp 3-day deletion timer. Files are
byte-identical copies of the /tmp originals — no edits, no reformatting.
Verified by sha256 after copy.

Recon population: `tours-data.json` → `_unknownFields.priceSource`, 384 stamped
rows across 4 distinct stamps. Rows whose writer was not in the tracked tree:
331 (claimed 331, delta 0).

| stamp | rows | tracked writer | status |
|---|---|---|---|
| fh-price-preview-v2-2026-08-20 | 198 | none | **rescued** (this dir) |
| fh-price-preview-v2-2026-08-22 | 133 | none | **unrecoverable** — no /tmp script writes it |
| v52-dominant-gate | 41 | scripts-staging/apply-v52-live-kwst.js (+ extract-price-v5.2.js, run-v52-kwst-dryrun.js) | already tracked |
| fh-price-preview-charter-2026-08-24 | 12 | scripts/fix-charter-maxtier.py | already tracked |

## write_backfill.py

- sha256: `df5bef01b4abebd555e4fffb7bb90544d5534d5abedea4c07154f4358d71e37b`
- original path: `/private/tmp/claude-501/-Users-jasondudney-repos-keywestsandbartours/d33ebf2f-0774-41a0-a9fa-faff89978da0/scratchpad/bf/write_backfill.py`
- size: 1529 bytes
- mtime: 2026-08-20T18:43:07 (local)
- writes stamp: `fh-price-preview-v2-2026-08-20` (hard-coded, line 24)
- rows accounted for: 198 — re-derived two ways: 198 rows in tours-data.json
  carry the stamp; the script's input `classified2.json` has 105 bucket-a +
  93 bucket-b = 198 rows. Shipped as commit 2fdce35 (#215).
- runtime dependency NOT rescued: `classified2.json` (382,279 bytes, same /tmp
  dir) — generated data, not a writer. The script is a record of *how* the
  stamp/fields were written, not re-runnable without that input.

## Unrecoverable: fh-price-preview-v2-2026-08-22 (133 rows)

Shipped in 9e1cb71 (#225, 3 rows) and e28b100 (#226, 130 rows); neither
commit included a script, and a full sweep of /private/tmp for the literal
stamp, the `fh-price-preview-v2` prefix, and any `priceSource` assignment
found no writer. Not reconstructed from memory — recorded here as lost.

## classified2.json (runtime input for write_backfill.py)

Rescued 2026-08-24 (s44, follow-up to #241) — the generated input the writer
reads; without it the script above is a record, not a re-run.

- sha256: `763fcc870acdc20b19bc6ab9db10df95706be6e32fa5bed8c0dc37cbec554580`
- original path: `/private/tmp/claude-501/-Users-jasondudney-repos-keywestsandbartours/d33ebf2f-0774-41a0-a9fa-faff89978da0/scratchpad/bf/classified2.json`
- size: 382,279 bytes
- mtime: 2026-08-20T18:42:29 (local) — 38 s before write_backfill.py's mtime
- role: runtime input for `write_backfill.py` / stamp `fh-price-preview-v2-2026-08-20`
- rows accounted for: 198 — 724 entries, buckets a=105, b=93, c=145, e=334,
  f=47; the writer applies only a+b = 198 distinct pks, and those 198 pks are
  exactly the 198 rows in tours-data.json carrying the stamp (0 either side).
- copied with `cp -p`, `cmp` byte-identical, sha256 re-verified post-copy.
