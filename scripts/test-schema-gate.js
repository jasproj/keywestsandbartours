#!/usr/bin/env node
// s53 schema price-unit gate test — run: node scripts/test-schema-gate.js
//
// Proves, against the REAL app.js and the REAL tours-data.json:
//   1. a known per-person row emits Offer.price byte-identical to the pre-s53 emitter
//   2. a known whole-boat row emits a UnitPriceSpecification whose unitText is the
//      exact string the card renders (same field, same trim)
//   3. a known no-evidence row emits no price at all
//   4. the three states partition the emitting population exactly — no row in two
//      states, no row in none — and no row emits a bare Offer.price outside state 1.
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

const root = path.join(__dirname, '..');

// app.js is a browser script; give it just enough DOM to load. Nothing here is
// invoked beyond addEventListener registration.
const noop = () => {};
const fakeEl = () => ({ style: {}, addEventListener: noop, appendChild: noop, textContent: '' });
const sandbox = {
    console,
    fetch: () => new Promise(noop),
    gtag: noop,
    document: {
        addEventListener: noop,
        querySelector: () => null,
        querySelectorAll: () => [],
        getElementById: () => null,
        createElement: fakeEl,
        body: fakeEl(),
        head: fakeEl(),
    },
    window: { addEventListener: noop },
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(root, 'app.js'), 'utf8'), sandbox, { filename: 'app.js' });

const { generateTourSchema, classifySchemaPriceUnit, hasUsablePrice, priceUnit } = sandbox;
assert.strictEqual(typeof generateTourSchema, 'function', 'generateTourSchema not found in app.js');
assert.strictEqual(typeof classifySchemaPriceUnit, 'function', 'classifySchemaPriceUnit not found in app.js');
assert.strictEqual(typeof hasUsablePrice, 'function', 'hasUsablePrice not found in app.js');
assert.strictEqual(typeof priceUnit, 'function', 'priceUnit not found in app.js');

// The pre-s53 emitter, frozen verbatim from commit 8327838, as the
// byte-identity oracle for state 1.
function legacyGenerateTourSchema(tour) {
    const emitPrice = Number.isFinite(tour.price) && tour.priceConfidence !== 'low';
    return {
        "@context": "https://schema.org",
        "@type": "TouristTrip",
        "name": tour.name,
        "description": tour.description || "",
        "touristType": tour.tags ? tour.tags.join(", ") : "",
        ...(emitPrice && {
            "offers": {
                "@type": "Offer",
                "price": tour.price,
                "priceCurrency": "USD",
                "url": tour.bookingUrl,
                "availability": "https://schema.org/InStock"
            }
        }),
        "provider": {
            "@type": "LocalBusiness",
            "name": tour.company
        }
    };
}

const raw = JSON.parse(fs.readFileSync(path.join(root, 'tours-data.json'), 'utf8'));
const tours = Array.isArray(raw) ? raw : raw.tours;
// The population the render path actually hands to createTourCard (init/initAreaPage).
const emitting = tours
    .filter(t => t.status !== 'inactive' && !t.bookingDead && !t.hidden)
    .filter(hasUsablePrice);

// --- Synthetic fixtures: the three canonical firings, stable regardless of data drift ---
const base = { name: 'Fixture', description: 'd', tags: ['x'], company: 'Co', bookingUrl: 'https://example.com/b', priceConfidence: 'verified' };
const fxPerPerson = { ...base, price: 59.95, priceLabel: 'Adult', _unknownFields: { priceUnit: 'per person' } };
const fxWholeBoat = { ...base, price: 1500, priceLabel: 'Two Hour Charter', _unknownFields: { priceUnit: 'whole boat · up to 6 passengers' } };
const fxNoEvidence = { ...base, price: 900, priceLabel: '', _unknownFields: {} };

{
    const got = generateTourSchema(fxPerPerson);
    assert.strictEqual(JSON.stringify(got), JSON.stringify(legacyGenerateTourSchema(fxPerPerson)),
        'per-person fixture: not byte-identical to pre-s53 emission');
    assert.strictEqual(got.offers.price, 59.95);
    assert.ok(!('priceSpecification' in got.offers));
    console.log('PASS fixture state 1 (per-person): offers = ' + JSON.stringify(got.offers));
}
{
    const got = generateTourSchema(fxWholeBoat);
    assert.ok(got.offers, 'whole-boat fixture must still carry an offers block');
    assert.ok(!('price' in got.offers), 'whole-boat fixture must not emit bare Offer.price');
    assert.strictEqual(JSON.stringify(got.offers.priceSpecification),
        JSON.stringify({ "@type": "UnitPriceSpecification", "price": 1500, "priceCurrency": "USD", "unitText": "whole boat · up to 6 passengers" }));
    console.log('PASS fixture state 2 (whole-boat): offers = ' + JSON.stringify(got.offers));
}
{
    const got = generateTourSchema(fxNoEvidence);
    assert.ok(!('offers' in got), 'no-evidence fixture must emit no price at all');
    assert.ok(!JSON.stringify(got).includes('"price"'));
    console.log('PASS fixture state 3 (no evidence): offers key absent');
}

// --- Known live rows (pks verified 2026-08-27; falls back to a dynamic pick if the data moves) ---
function pick(pk, predicate) {
    const row = emitting.find(t => t.pk === pk);
    return (row && predicate(row)) ? row : emitting.find(predicate);
}
const livePP = pick(748863, t => classifySchemaPriceUnit(t) === 'per-person' && priceUnit(t) === 'per person');
const liveWB = pick(130505, t => classifySchemaPriceUnit(t) === 'non-per-person' && priceUnit(t).indexOf('whole boat') === 0);
const liveNoEv = pick(622775, t => classifySchemaPriceUnit(t) === 'unknown');
assert.ok(livePP && liveWB && liveNoEv, 'live witnesses not found');

assert.strictEqual(JSON.stringify(generateTourSchema(livePP)), JSON.stringify(legacyGenerateTourSchema(livePP)),
    'live per-person pk ' + livePP.pk + ': schema bytes changed');
console.log('PASS live state 1 pk ' + livePP.pk + ': byte-identical schema, offers = ' + JSON.stringify(generateTourSchema(livePP).offers));

const wbSchema = generateTourSchema(liveWB);
assert.ok(!('price' in wbSchema.offers), 'live whole-boat row leaked a bare price');
assert.strictEqual(wbSchema.offers.priceSpecification.unitText, liveWB._unknownFields.priceUnit.trim(),
    'unitText must be the exact card string');
assert.strictEqual(wbSchema.offers.priceSpecification.price, liveWB.price);
console.log('PASS live state 2 pk ' + liveWB.pk + ': offers = ' + JSON.stringify(wbSchema.offers));

const noEvSchema = generateTourSchema(liveNoEv);
assert.ok(!('offers' in noEvSchema), 'no-evidence row leaked a price');
console.log('PASS live state 3 pk ' + liveNoEv.pk + ': offers key absent');

// --- Full-population sweep: partition + emission invariants ---
const counts = { 'per-person': 0, 'non-per-person': 0, 'unknown': 0 };
const face = { 'per-person': 0, 'non-per-person': 0, 'unknown': 0 };
let nppWithUnit = 0;
for (const t of emitting) {
    const state = classifySchemaPriceUnit(t);
    assert.ok(state in counts, 'pk ' + t.pk + ': classifier returned unexpected state ' + state);
    counts[state]++;
    face[state] += t.price;
    const schema = generateTourSchema(t);
    if (state === 'per-person') {
        assert.ok(schema.offers && 'price' in schema.offers && !('priceSpecification' in schema.offers),
            'pk ' + t.pk + ': state 1 emission wrong');
        assert.strictEqual(JSON.stringify(schema), JSON.stringify(legacyGenerateTourSchema(t)),
            'pk ' + t.pk + ': state 1 must be byte-identical to pre-s53');
    } else if (state === 'non-per-person' && priceUnit(t)) {
        nppWithUnit++;
        assert.ok(schema.offers && !('price' in schema.offers), 'pk ' + t.pk + ': state 2 leaked a bare price');
        assert.strictEqual(schema.offers.priceSpecification.unitText, priceUnit(t),
            'pk ' + t.pk + ': unitText differs from the card string');
        assert.strictEqual(schema.offers.priceSpecification.price, t.price);
    } else {
        // state 3, and state-2 rows with no card unit string to mirror
        assert.ok(!('offers' in schema), 'pk ' + t.pk + ': state ' + state + ' with no card unit must emit no price');
    }
}
const total = counts['per-person'] + counts['non-per-person'] + counts['unknown'];
assert.strictEqual(total, emitting.length, 'states do not partition the emitting population');
console.log('PASS partition: every emitting row in exactly one state, no bare price outside state 1');
console.log(JSON.stringify({
    population: emitting.length,
    counts,
    faceUSD: { 'per-person': Math.round(face['per-person']), 'non-per-person': Math.round(face['non-per-person']), 'unknown': Math.round(face['unknown']) },
    nonPerPersonWithCardUnit: nppWithUnit,
}, null, 2));
console.log('ALL TESTS PASSED');
