#!/usr/bin/env node
// s53 static-grid hydration test — run: node scripts/test-static-grid-hydration.js
//
// Proves, against the REAL app.js and the REAL tours-data.json (islamorada pool):
//   A. an unstamped grid still takes the replace path (innerHTML rewritten)
//   B. a stamped grid whose baked pk set equals the pool is HYDRATED in place:
//      innerHTML untouched, cards reordered to filteredTours order, filtered-out
//      cards hidden, no pagination, load-more hidden, count text correct,
//      empty-filter message shown without destroying the baked cards
//   C. a stamped grid whose pk set differs from the pool falls back to replace
//   D. createTourCard-style cards keyed by data-id hydrate the same way
//   E. loadMore() on a hydrated grid changes nothing
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

const root = path.join(__dirname, '..');

// --- a minimal DOM: just enough for renderTours()/loadMore() to act on ---
class El {
    constructor(tag, attrs) {
        this.tagName = tag; this.attrs = Object.assign({}, attrs || {}); this.children = []; this.parent = null;
        this.style = {}; this.className = this.attrs.class || ''; this.textContent = ''; this._innerHTML = '';
    }
    hasAttribute(n) { return Object.prototype.hasOwnProperty.call(this.attrs, n); }
    getAttribute(n) { return this.hasAttribute(n) ? this.attrs[n] : null; }
    setAttribute(n, v) { this.attrs[n] = String(v); }
    appendChild(c) {
        if (c.parent) c.parent.children.splice(c.parent.children.indexOf(c), 1);
        c.parent = this; this.children.push(c); return c;
    }
    querySelectorAll(sel) {
        const cls = sel.slice(1); const out = [];
        const walk = (n) => { for (const c of n.children) { if ((c.className || '').split(/\s+/).includes(cls)) out.push(c); walk(c); } };
        walk(this); return out;
    }
    querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
    get innerHTML() { return this._innerHTML; }
    set innerHTML(v) { this._innerHTML = v; for (const c of this.children) c.parent = null; this.children = []; }
    addEventListener() {}
}
const byId = {};
const noop = () => {};
const sandbox = {
    console, gtag: noop, fetch: () => new Promise(noop),
    document: {
        getElementById: (id) => byId[id] || null,
        querySelector: () => null, querySelectorAll: () => [], addEventListener: noop,
        createElement: (tag) => new El(tag), body: new El('body'), head: new El('head'),
    },
    window: { addEventListener: noop },
    sessionStorage: { getItem: () => null, setItem: noop, removeItem: noop },
    localStorage: { getItem: () => null, setItem: noop, removeItem: noop },
};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(root, 'app.js'), 'utf8'), sandbox, { filename: 'app.js' });
const { hasUsablePrice, getArea, hydratableGrid } = sandbox;
assert.strictEqual(typeof hydratableGrid, 'function', 'hydratableGrid not found in app.js');

// The islamorada pool, by the site's own predicate (same filters initAreaPage applies).
const raw = JSON.parse(fs.readFileSync(path.join(root, 'tours-data.json'), 'utf8'));
const pool = (Array.isArray(raw) ? raw : raw.tours)
    .filter(t => t.status !== 'inactive' && !t.bookingDead && !t.hidden)
    .filter(hasUsablePrice)
    .filter(t => getArea(t.location) === 'islamorada');
assert.ok(pool.length > 0, 'islamorada pool is empty');
console.log('islamorada pool by the site predicate: ' + pool.length + ' rows');

function bakedGrid(rows, keyAttr, stamp) {
    const grid = new El('div', Object.assign({ id: 'tours-grid', class: 'tours-grid' }, stamp ? { 'data-generated-from': 'a'.repeat(64) } : {}));
    // generator order: qualityScore desc, pk asc
    const ordered = [...rows].sort((a, b) => ((b.qualityScore || 0) - (a.qualityScore || 0)) || (a.pk - b.pk));
    for (const t of ordered) grid.appendChild(new El('article', { class: 'tour-card', [keyAttr]: String(t.pk) }));
    return grid;
}
function mount(grid) {
    byId['tours-grid'] = grid;
    byId['load-more'] = new El('button', { id: 'load-more' });
    byId['tours-count'] = new El('span', { id: 'tours-count' });
}
function setState(all, filtered) {
    sandbox.__all = all; sandbox.__filtered = filtered;
    vm.runInContext('allTours = __all; filteredTours = __filtered; displayedCount = 0;', sandbox);
}
const order = (grid) => grid.children.filter(c => c.className.includes('tour-card') && c.style.display !== 'none').map(c => c.getAttribute('data-pk') || c.getAttribute('data-id'));

// A. unstamped grid -> replace path
{
    const grid = bakedGrid(pool, 'data-pk', false); mount(grid);
    setState(pool, pool);
    vm.runInContext('renderTours()', sandbox);
    assert.ok(grid.innerHTML.includes('tour-card'), 'A: replace path must rewrite innerHTML');
    assert.strictEqual(grid.children.length, 0, 'A: baked children must be gone after replace');
    console.log('PASS A: unstamped grid takes the replace path');
}

// B. stamped, pk set == pool -> hydrate
{
    const grid = bakedGrid(pool, 'data-pk', true); mount(grid);
    const shuffled = [...pool].reverse();
    setState(pool, shuffled);
    vm.runInContext('renderTours()', sandbox);
    assert.strictEqual(grid.innerHTML, '', 'B: hydration must not touch innerHTML');
    assert.strictEqual(grid.children.length, pool.length, 'B: every baked card still present');
    assert.deepStrictEqual(order(grid), shuffled.map(t => String(t.pk)), 'B: cards must be reordered to filteredTours order');
    assert.strictEqual(byId['load-more'].style.display, 'none', 'B: load-more must be hidden (no pagination)');
    assert.strictEqual(byId['tours-count'].textContent, `Showing ${pool.length} of ${pool.length} tours`, 'B: count text');
    assert.strictEqual(vm.runInContext('displayedCount', sandbox), pool.length, 'B: displayedCount = whole set, not TOURS_PER_PAGE');

    const ten = shuffled.slice(0, 10);
    setState(pool, ten);
    vm.runInContext('renderTours()', sandbox);
    assert.deepStrictEqual(order(grid), ten.map(t => String(t.pk)), 'B: filtered order');
    assert.strictEqual(grid.children.filter(c => c.className.includes('tour-card') && c.style.display === 'none').length, pool.length - 10, 'B: filtered-out cards hidden, not removed');
    assert.strictEqual(byId['tours-count'].textContent, `Showing 10 of 10 tours`, 'B: filtered count text');

    setState(pool, []);
    vm.runInContext('renderTours()', sandbox);
    assert.strictEqual(order(grid).length, 0, 'B: nothing visible on empty filter');
    const empty = grid.querySelector('.tours-empty');
    assert.ok(empty && empty.style.display === '', 'B: empty message shown');
    assert.strictEqual(grid.children.filter(c => c.className.includes('tour-card')).length, pool.length, 'B: baked cards survive an empty filter');

    setState(pool, shuffled);
    vm.runInContext('renderTours()', sandbox);
    assert.strictEqual(grid.querySelector('.tours-empty').style.display, 'none', 'B: empty message hidden again');
    assert.strictEqual(order(grid).length, pool.length, 'B: all cards back');
    console.log('PASS B: stamped grid with matching pk set is hydrated in place (reorder, show/hide, no pagination, empty state)');
}

// C. stamped, pk set != pool -> replace path
{
    const grid = bakedGrid(pool.slice(1), 'data-pk', true); mount(grid);
    setState(pool, pool);
    vm.runInContext('renderTours()', sandbox);
    assert.ok(grid.innerHTML.includes('tour-card'), 'C: mismatched bake must fall back to replace');
    console.log('PASS C: stamped grid with a differing pk set falls back to the replace path');
}

// D. data-id keyed cards (createTourCard markup) hydrate too
{
    const grid = bakedGrid(pool, 'data-id', true); mount(grid);
    setState(pool, pool);
    vm.runInContext('renderTours()', sandbox);
    assert.strictEqual(grid.innerHTML, '', 'D: data-id keyed grid must hydrate');
    assert.deepStrictEqual(order(grid), pool.map(t => String(t.pk)), 'D: order');
    console.log('PASS D: data-id keyed cards hydrate');
}

// E. loadMore on a hydrated grid is a no-op
{
    const grid = bakedGrid(pool, 'data-pk', true); mount(grid);
    setState(pool, pool);
    vm.runInContext('renderTours(); loadMore();', sandbox);
    assert.strictEqual(grid.innerHTML, '', 'E: loadMore must not append to a hydrated grid');
    assert.strictEqual(grid.children.length, pool.length, 'E: card count unchanged');
    console.log('PASS E: loadMore is a no-op on a hydrated grid');
}

console.log('ALL TESTS PASSED');
