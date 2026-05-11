#!/usr/bin/env node
/**
 * KWST-specific metadata-preamble stripper.
 * KWST FareHarbor pages use different divider vocabulary than WHAW
 * (no "Activity details" header). Patterns observed in 5 dry-run samples:
 *   - "About:\n" prefix (snorkeling-style)
 *   - "About\n" prefix (try-scuba, pontoon)
 *   - "Prices for {date}\n" date-stamp tail (sunset-cruise, fishmonster)
 *
 * Trailing cruft markers cut everything from first match to end:
 *   Cancellations / What's (not) included / Itinerary / Highlights /
 *   Additional information / Overview / Meeting point / Group size
 *
 * Output policy:
 *   - prose ≥40 chars after strip → use stripped
 *   - prose <40 chars → 'low-content', leave empty
 *   - no divider matches → 'no-divider', leave empty
 *
 * Usage: node strip-metadata-preamble-kwst.js <input.json> [<output.json>]
 *   default input  = /tmp/kwst-empty-desc-rescrape.json
 *   default output = /tmp/kwst-empty-desc-cleaned.json
 */

const fs = require('fs');

const INPUT  = process.argv[2] || '/tmp/kwst-empty-desc-rescrape.json';
const OUTPUT = process.argv[3] || '/tmp/kwst-empty-desc-cleaned.json';
const MIN_LEN = 40;

const DIVIDERS = [
  { name: 'About:',      re: /\bAbout:\s*\n+/ },
  { name: 'About',       re: /\bAbout\s*\n+/ },
  { name: 'PricesFor',   re: /\bPrices for [^.\n]+\.\s*\n+/ },
];

const TRAIL_CRUFT_RE = /\n+(?:Cancellations?(?:\s+policy)?|What's\s+(?:not\s+)?included|Itinerary|Highlights|Additional\s+information|Overview|Meeting\s+point|Group\s+size|Duration\s*\n|Pricing|Rates|Trip\s+Times|More\s+info)\b/i;

function clean(desc) {
  if (!desc) return { result: '', action: 'empty' };

  let dividerHit = null;
  let after = null;

  for (const d of DIVIDERS) {
    const m = desc.match(d.re);
    if (m) {
      dividerHit = d.name;
      after = desc.slice(m.index + m[0].length);
      break;
    }
  }

  if (!dividerHit) return { result: '', action: 'no-divider', dividerHit: null };

  const cruftMatch = after.match(TRAIL_CRUFT_RE);
  if (cruftMatch) after = after.slice(0, cruftMatch.index);

  after = after.replace(/\s+/g, ' ').trim();

  if (after.length < MIN_LEN) {
    return { result: '', action: 'low-content', dividerHit, prose_len: after.length };
  }

  return { result: after, action: 'cleaned', dividerHit, prose_len: after.length };
}

function main() {
  const raw = JSON.parse(fs.readFileSync(INPUT, 'utf8'));
  const tours = Array.isArray(raw) ? raw : (raw.tours || []);

  const stats = { cleaned: 0, 'low-content': 0, 'no-divider': 0, empty: 0 };
  const dividerCounts = {};
  const samples = { cleaned: [], 'low-content': [], 'no-divider': [] };

  for (const t of tours) {
    const out = clean(t.description);
    stats[out.action]++;
    if (out.dividerHit) dividerCounts[out.dividerHit] = (dividerCounts[out.dividerHit] || 0) + 1;

    if (samples[out.action] && samples[out.action].length < 5) {
      samples[out.action].push({
        id: t.id,
        name: (t.name || '').slice(0, 60),
        divider: out.dividerHit,
        before_len: (t.description || '').length,
        after_len: out.result.length,
        after_preview: out.result.slice(0, 220),
      });
    }

    t.description = out.result;
  }

  fs.writeFileSync(OUTPUT, JSON.stringify(tours, null, 2));

  console.log(`\n=== INPUT  ${INPUT}`);
  console.log(`=== OUTPUT ${OUTPUT}`);
  console.log(`=== TOTAL  ${tours.length} tours`);
  console.log('\n=== STATS ===');
  console.log(JSON.stringify(stats, null, 2));
  console.log('\n=== DIVIDER COUNTS ===');
  console.log(JSON.stringify(dividerCounts, null, 2));
  console.log('\n=== CLEANED SAMPLES (up to 5) ===');
  console.log(JSON.stringify(samples.cleaned, null, 2));
  console.log('\n=== LOW-CONTENT SAMPLES ===');
  console.log(JSON.stringify(samples['low-content'], null, 2));
  console.log('\n=== NO-DIVIDER SAMPLES ===');
  console.log(JSON.stringify(samples['no-divider'], null, 2));
}

main();
