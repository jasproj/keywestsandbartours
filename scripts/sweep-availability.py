#!/usr/bin/env python3
"""sweep-availability.py — per-tour live-availability sweep for tours-data.json.

DATA COLLECTION ONLY. This script does not hide, filter, or retire any tour.
(It does UN-hide: a row carrying the human-ruled `hidden: true` — see
scripts/s51-kwst-hide-apply.py — is cleared to hidden: false the moment the
endpoint returns a bookable date for it. Hiding stays human-ruled; only the
reversal is automatic, because the date is the evidence the hide rested on.)
It persists two new fields per active record so a future hide/retire pass has
real per-item data to work from, instead of guessing from name/description
keywords — a keyword sweep during recon false-positived on generic marketing
copy ("book your event") on non-event products, and undercounted because most
staleness turned out to not be holiday-named at all.

Fields added (schema ADDITIONS only — no existing field is renamed or moved):
  nextAvailableDate    ISO date string of the item's next bookable date, or
                       null if FareHarbor reports none. Source: FareHarbor's
                       public per-item embed endpoint (see SOURCE below).
  nullConsecutiveSweeps  Increments each run nextAvailableDate comes back
                       null; resets to 0 the moment a date is found. Mirrors
                       the existing statusConsecutiveRuns pattern so a single
                       transient null (operator recalendaring, a slow day)
                       doesn't look the same as sustained deadness.

SOURCE — GET https://fareharbor.com/api/embed/{shortname}/next-bookable-availability/v1/?date={YYYY-MM-DD}&item_pks={pk}
  Reverse-engineered from the embed page's own JS bundle (not documented).
  Returns {"next_available_date": "YYYY-MM-DD"} or {"next_available_date": null}.
  Passing multiple item_pks returns ONE aggregate date for the whole batch,
  not one per item — confirmed by probing an operator with 3 items at once
  vs individually. That makes batching unsafe for this purpose (it would
  mask an individually-dead item sitting next to a live sibling), so this
  script calls the endpoint once per item, not once per operator.

KNOWN FALSE-POSITIVE CLASS — do not build hide logic on this data alone.
  A manual read of a stratified probe sample found ~35-40% of null-date hits
  are NOT dead: they're inherently custom/inquiry-only products (wedding
  photography, multi-day private charters) that will show null forever
  because they never populate a self-serve calendar by design, not because
  they're abandoned. No FareHarbor item-level flag reliably separates these
  from genuinely-lapsed listings (is_bookable_ever_by_phone and
  is_cutoff_unreached_call_to_book are inconsistent on both sides in
  practice). data/operator-allowlist.json exempts operators confirmed to be
  in this class; extend it by hand as more are found, not by inferring a
  rule from item fields.

Only ACTIVE records are swept (status == "active"). tours-data.json has zero
records where status == "active" and bookingDead == true, so this is the
same population the rest of the codebase calls "live".

Modes (exactly one required):
  --dry-run   Run the full network sweep, print the report, write nothing.
  --live      Run the full network sweep, print the report, write
              tours-data.json.
  --report    No network calls. Read tours-data.json as already swept and
              print the would-hide list: active AND nextAvailableDate is
              null AND nullConsecutiveSweeps >= 2 AND operator not in
              data/operator-allowlist.json. Prints only — never writes,
              never hides anything. This is recon output for a future,
              separate hide/retire decision.

  --limit N   Cap the swept population to the first N active records
              (after allowlist is still applied at report time). For
              development iteration only; the recorded --dry-run and
              --live runs for this PR used the full population.
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOURS_DATA = REPO / "tours-data.json"
ALLOWLIST_PATH = REPO / "data" / "operator-allowlist.json"
UA = {"User-Agent": "Mozilla/5.0 WanderRenderMonitor/1.0 (+internal-qa)"}
ENDPOINT = "https://fareharbor.com/api/embed/{sn}/next-bookable-availability/v1/?date={date}&item_pks={pk}"
WORKERS = 8
NULL_HIDE_THRESHOLD = 2

SHORTNAME_RE = re.compile(r"/embeds/book/([^/]+)/items/(\d+)")


def load_tours():
    return json.loads(TOURS_DATA.read_text())


def load_allowlist():
    if not ALLOWLIST_PATH.exists():
        return set()
    data = json.loads(ALLOWLIST_PATH.read_text())
    return set(data.get("operators", {}).keys())


def shortname_of(booking_url):
    m = SHORTNAME_RE.search(booking_url or "")
    return m.group(1) if m else None


def probe(shortname, pk, date):
    url = ENDPOINT.format(sn=shortname, date=date, pk=pk)
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return "error", None, f"HTTP {e.code}"
    except Exception as e:
        return "error", None, str(e)
    if status != 200:
        return "error", None, f"HTTP {status}"
    try:
        parsed = json.loads(body)
    except Exception as e:
        return "error", None, f"parse-error: {e}"
    return "ok", parsed.get("next_available_date"), None


def sweep(tours, limit=None):
    active = [t for t in tours if t.get("status") == "active"]
    if limit:
        active = active[:limit]

    jobs = []
    skipped_no_shortname = 0
    for t in active:
        sn = shortname_of(t.get("bookingUrl"))
        if not sn:
            skipped_no_shortname += 1
            continue
        jobs.append((t, sn))

    today = datetime.now(timezone.utc).date().isoformat()
    results = {}  # pk -> (outcome, next_date, err)

    def run_one(job):
        t, sn = job
        outcome, next_date, err = probe(sn, t["pk"], today)
        return t["pk"], outcome, next_date, err

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = [ex.submit(run_one, job) for job in jobs]
        done = 0
        for fut in as_completed(futures):
            pk, outcome, next_date, err = fut.result()
            results[pk] = (outcome, next_date, err)
            done += 1
            if done % 100 == 0:
                print(f"  ...{done}/{len(jobs)} probed", file=sys.stderr)

    return active, results, skipped_no_shortname, today


def apply_results(tours, results, date_used):
    """Mutates active records in place with the new fields. Returns stats."""
    got_date = 0
    null_count = 0
    error_count = 0
    unhidden = 0
    null_by_operator = Counter()

    for t in tours:
        pk = t.get("pk")
        if pk not in results:
            continue
        outcome, next_date, err = results[pk]
        if outcome == "error":
            error_count += 1
            continue
        prev_null_sweeps = t.get("nullConsecutiveSweeps") or 0
        if next_date is None:
            t["nextAvailableDate"] = None
            t["nullConsecutiveSweeps"] = prev_null_sweeps + 1
            null_count += 1
            sn = shortname_of(t.get("bookingUrl")) or "unknown"
            null_by_operator[sn] += 1
        else:
            t["nextAvailableDate"] = next_date
            t["nullConsecutiveSweeps"] = 0
            got_date += 1
            if t.get("hidden"):
                # Reversal path for the human-ruled hide (s51): a bookable date is the
                # evidence the hide was keyed on, so its return clears the hide. The
                # reason stamp is kept for the audit trail, prefixed with the reversal.
                t["hidden"] = False
                t["hiddenReason"] = f"UNHIDDEN by sweep {date_used}: next_available_date={next_date}. Was: " + str(t.get("hiddenReason") or "")
                unhidden += 1

    return {
        "got_date": got_date,
        "null_count": null_count,
        "error_count": error_count,
        "unhidden": unhidden,
        "null_by_operator": null_by_operator,
    }


def print_sweep_report(stats, swept_count, skipped_no_shortname, date_used):
    print()
    print("=== SWEEP REPORT ===")
    print(f"Date probed: {date_used}")
    print(f"Un-hidden (hidden:true rows whose bookable date returned): {stats.get('unhidden', 0)}")
    print(f"Active records considered: {swept_count}")
    if skipped_no_shortname:
        print(f"Skipped (unparseable bookingUrl): {skipped_no_shortname}")
    print(f"Got a next-available date: {stats['got_date']}")
    print(f"Null (no future date): {stats['null_count']}")
    print(f"Errors (left untouched): {stats['error_count']}")
    if stats["null_by_operator"]:
        print()
        print("Top operators in the null set:")
        for sn, cnt in stats["null_by_operator"].most_common(15):
            print(f"  {cnt:4d}  {sn}")


def cmd_sweep(args):
    envelope = load_tours()
    tours = envelope["tours"]
    active, results, skipped_no_shortname, date_used = sweep(tours, limit=args.limit)
    stats = apply_results(tours, results, date_used)
    print_sweep_report(stats, len(active), skipped_no_shortname, date_used)

    if args.live:
        TOURS_DATA.write_text(json.dumps(envelope, indent=2) + "\n")
        print()
        print(f"WROTE {TOURS_DATA}")
    else:
        print()
        print("DRY RUN — tours-data.json NOT written.")


def cmd_report(args):
    envelope = load_tours()
    tours = envelope["tours"]
    allowlist = load_allowlist()

    would_hide = []
    for t in tours:
        if t.get("status") != "active":
            continue
        if t.get("nextAvailableDate") is not None:
            continue
        if (t.get("nullConsecutiveSweeps") or 0) < NULL_HIDE_THRESHOLD:
            continue
        if t.get("hidden"):
            continue  # already hidden by a human ruling; not a candidate again
        sn = shortname_of(t.get("bookingUrl"))
        if sn in allowlist:
            continue
        would_hide.append((t, sn))

    print("=== WOULD-HIDE REPORT (report only — nothing hidden, nothing written) ===")
    print(f"Criteria: status == active AND nextAvailableDate == null AND "
          f"nullConsecutiveSweeps >= {NULL_HIDE_THRESHOLD} AND operator not allowlisted")
    print(f"Total: {len(would_hide)}")
    print()
    by_operator = Counter(sn or "unknown" for _, sn in would_hide)
    for sn, cnt in by_operator.most_common(20):
        print(f"  {cnt:4d}  {sn}")
    print()
    for t, sn in would_hide[:50]:
        print(f"  pk={t['pk']:<8} sweeps={t.get('nullConsecutiveSweeps')!s:<3} "
              f"{sn:28s} {t.get('name')}")
    if len(would_hide) > 50:
        print(f"  ... and {len(would_hide) - 50} more")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Full sweep, print report, write nothing.")
    mode.add_argument("--live", action="store_true", help="Full sweep, print report, write tours-data.json.")
    mode.add_argument("--report", action="store_true", help="No network. Print the would-hide list from already-swept data.")
    parser.add_argument("--limit", type=int, default=None, help="Cap swept population (sweep modes only; development use).")
    args = parser.parse_args()

    if args.report:
        cmd_report(args)
    else:
        cmd_sweep(args)


if __name__ == "__main__":
    main()
