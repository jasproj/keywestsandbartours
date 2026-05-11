#!/usr/bin/env node
/**
 * Enrichment scraper for tours-thin-and-empty.json with crash-safe checkpointing.
 *
 * - Reads:   tours-thin-and-empty.json
 * - Writes:  tours-thin-enriched.json (checkpointed every 50 tours)
 * - Resume:  if tours-thin-enriched.json exists, it is used as the working set
 *            and tours that already have description+price are skipped, so a
 *            crash mid-run can be recovered by simply re-launching the script.
 *
 * Usage:
 *   node enrich-thin.js                            # USD, full pass
 *   node enrich-thin.js --currency EUR --limit 50  # EUR test on first 50
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');
const { extract_price } = require('./extract-price-v5');

const INPUT_FILE = '/tmp/kwst-empty-desc-tours.json';
const OUTPUT_FILE = '/tmp/kwst-empty-desc-rescrape.json';
const CHECKPOINT_EVERY = 50;

const args = process.argv.slice(2);
const LIMIT = args.includes('--limit')
  ? parseInt(args[args.indexOf('--limit') + 1], 10)
  : Infinity;

const currencyArg = args.find((a, i) => args[i-1] === '--currency');
const CURRENCY = currencyArg || 'USD';
const VALID_CURRENCIES = ['USD', 'EUR', 'GBP', 'NZD'];
if (!VALID_CURRENCIES.includes(CURRENCY)) {
  console.error(`Invalid currency: ${CURRENCY}. Must be one of: ${VALID_CURRENCIES.join(', ')}`);
  process.exit(1);
}
console.log(`Currency: ${CURRENCY}`);
console.log(`Input:  ${INPUT_FILE}`);
console.log(`Output: ${OUTPUT_FILE} (checkpoint every ${CHECKPOINT_EVERY} tours)`);

function writeCheckpoint(workingSet, sourceWasArray, sourceData) {
  const finalOutput = sourceWasArray ? workingSet : { ...sourceData, tours: workingSet };
  const tmp = OUTPUT_FILE + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(finalOutput, null, 2));
  fs.renameSync(tmp, OUTPUT_FILE);
}

async function extractTourFields(page) {
  return await page.evaluate(() => {
    const result = {
      pageText: document.body.innerText,
      description: null,
      duration: null,
      capacity: null,
      galleryImages: [],
      highlights: []
    };

    const article = document.querySelector('main article') || document.querySelector('article') || document.querySelector('main');
    if (article) {
      const articleText = article.innerText || '';
      const descMatch = articleText.match(/(?:Description|About this (?:tour|experience|activity))\s*\n+([\s\S]{50,2000}?)(?=\n\n[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s*\n|$)/i);
      if (descMatch) {
        result.description = descMatch[1].trim();
      } else {
        const cleaned = articleText.replace(/^\s*\S+.*\n+/g, '').trim();
        if (cleaned.length > 80) {
          result.description = cleaned.substring(0, 1500).trim();
        }
      }
    }

    const durMatch = result.pageText.match(/Duration[:\s]+(\d+(?:\.\d+)?\s*(?:hours?|hrs?|minutes?|mins?|days?)(?:\s+(?:and|&)\s+\d+\s*(?:minutes?|mins?))?)/i);
    if (durMatch) result.duration = durMatch[1].trim();

    const capMatch = result.pageText.match(/(?:Capacity|Group size|Max(?:imum)?\s+(?:guests?|people|participants?))[:\s]+(?:Up to\s+)?(\d+)/i);
    if (capMatch) result.capacity = parseInt(capMatch[1], 10);

    if (article) {
      const imgs = [...article.querySelectorAll('img')];
      result.galleryImages = imgs
        .map(img => img.src || img.getAttribute('data-src'))
        .filter(src => src && (src.includes('fareharbor.com') || src.includes('fareharborcdn.com') || src.includes('cloudfront')))
        .filter(src => !src.includes('logo') && !src.includes('icon'))
        .filter((v, i, a) => a.indexOf(v) === i)
        .slice(0, 12);
    }

    if (article) {
      const lis = [...article.querySelectorAll('li')]
        .map(li => (li.innerText || '').trim())
        .filter(t => t.length > 10 && t.length < 200)
        .slice(0, 8);
      result.highlights = lis;
    }

    return result;
  });
}

async function main() {
  const sourceData = JSON.parse(fs.readFileSync(INPUT_FILE, 'utf8'));
  const sourceWasArray = Array.isArray(sourceData);
  const sourceTours = sourceWasArray ? sourceData : (sourceData.tours || []);

  let workingSet;
  if (fs.existsSync(OUTPUT_FILE)) {
    const prior = JSON.parse(fs.readFileSync(OUTPUT_FILE, 'utf8'));
    const priorTours = Array.isArray(prior) ? prior : (prior.tours || []);
    const byId = new Map(priorTours.map(t => [t.id, t]));
    workingSet = sourceTours.map(t => byId.get(t.id) || { ...t });
    console.log(`Resuming from existing ${OUTPUT_FILE} (${priorTours.length} prior records merged)`);
  } else {
    workingSet = sourceTours.map(t => ({ ...t }));
  }

  const candidates = workingSet
    .map((t, idx) => ({ t, idx }))
    .filter(({ t }) => t.bookingLink || t.url || t.fareharborUrl || t.bookingUrl)
    .filter(({ t }) => !(t.description && t.description.length > 50 && t.price));

  const targets = candidates.slice(0, LIMIT);
  console.log(`Total tours: ${workingSet.length}`);
  console.log(`Already enriched (skipped): ${workingSet.length - candidates.length}`);
  console.log(`To enrich this run: ${targets.length}`);

  if (targets.length === 0) {
    writeCheckpoint(workingSet, sourceWasArray, sourceData);
    console.log('Nothing to do.');
    return;
  }

  const browser = await chromium.launch({ headless: true });
  const browserContext = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
  });

  const stats = {
    high: 0, medium: 0, low: 0, none: 0, errors: 0,
    descGood: 0, descMissing: 0,
    durationFound: 0, capacityFound: 0,
    galleryFound: 0, highlightsFound: 0,
    checkpoints: 0
  };

  let processedSinceCheckpoint = 0;

  for (let i = 0; i < targets.length; i++) {
    const { t: tour } = targets[i];
    const url = tour.bookingLink || tour.url || tour.fareharborUrl || tour.bookingUrl;
    try {
      const page = await browserContext.newPage();
      await page.goto(url, { timeout: 30000, waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(3500);
      await page.waitForSelector('text=/Adults?|Pricing|Description|About/i', { timeout: 5000 }).catch(() => {});

      const fields = await extractTourFields(page);
      await page.close();

      const { price, priceConfidence, priceLabel } = extract_price(fields.pageText, CURRENCY);
      tour.price = price;
      tour.priceConfidence = priceConfidence;
      tour.priceLabel = priceLabel;
      if (price != null) tour.currency = CURRENCY;

      if (fields.description) {
        tour.description = fields.description;
        stats.descGood++;
      } else {
        stats.descMissing++;
      }

      if (fields.duration) { tour.duration = fields.duration; stats.durationFound++; }
      if (fields.capacity) { tour.capacity = fields.capacity; stats.capacityFound++; }
      if (fields.galleryImages.length > 0) {
        tour.galleryImages = fields.galleryImages;
        stats.galleryFound++;
      }
      if (fields.highlights.length > 0) {
        tour.highlights = fields.highlights;
        stats.highlightsFound++;
      }

      if (priceConfidence) stats[priceConfidence]++;
      else stats.none++;

      delete tour.scrapeError;

      if ((i + 1) % 25 === 0) {
        console.log(`  [${i + 1}/${targets.length}] price[h:${stats.high} m:${stats.medium} l:${stats.low} ø:${stats.none}] desc:${stats.descGood} dur:${stats.durationFound} cap:${stats.capacityFound} gal:${stats.galleryFound} err:${stats.errors}`);
      }
    } catch (err) {
      stats.errors++;
      tour.scrapeError = err.message.slice(0, 200);
    }

    processedSinceCheckpoint++;
    if (processedSinceCheckpoint >= CHECKPOINT_EVERY) {
      writeCheckpoint(workingSet, sourceWasArray, sourceData);
      stats.checkpoints++;
      processedSinceCheckpoint = 0;
      console.log(`  ↳ checkpoint #${stats.checkpoints} written (${i + 1}/${targets.length} processed)`);
    }
  }

  await browser.close();

  writeCheckpoint(workingSet, sourceWasArray, sourceData);

  console.log('\n✓ Enrichment complete');
  console.log(`  Price:        high:${stats.high} med:${stats.medium} low:${stats.low} none:${stats.none}`);
  console.log(`  Description:  found ${stats.descGood}, missing ${stats.descMissing}`);
  console.log(`  Duration found:    ${stats.durationFound}`);
  console.log(`  Capacity found:    ${stats.capacityFound}`);
  console.log(`  Gallery found:     ${stats.galleryFound}`);
  console.log(`  Highlights found:  ${stats.highlightsFound}`);
  console.log(`  Errors:            ${stats.errors}`);
  console.log(`  Checkpoints:       ${stats.checkpoints} (final write completed)`);
  console.log(`\nOutput: ${OUTPUT_FILE}`);
}

main().catch(e => { console.error(e); process.exit(1); });
