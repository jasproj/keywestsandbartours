#!/usr/bin/env python3
"""s51-kwst-backfill — price the unpriced active rows of tours-data.json from live FareHarbor ladders.

POPULATION (re-derived in-branch, asserted == 525 rows / 112 shortnames)
  status == 'active' AND price is None AND bookingUrl parses as fareharbor.com/embeds/book/<sn>/items/<pk>/
  (pk asserted == row pk on every row; 0 bookingDead in the population).

INSTRUMENT (probe mode; rules carried from scripts/probe-charter-ladders.py and the FST s50 port)
  price-preview/per-item/v2, include_breakdown=yes, <=20 pks per request, 1 req/s, 4 dated requests
  (2026-08-29 / 09-05 / 09-19 / 10-10), bounded retries (3, exponential backoff; 400/404 are answers,
  not retried). Item key is `id`, never `pk`. Absent from items[] = UNSAMPLED, never $0. $0 tiers are
  not fares (D-575). A reading is date-valid when start_at[0:10] == requested date; an echo-dated
  ladder is still live evidence and is recorded as a caveat (D-638). Falsifiability: an impossible
  shortname must not return 200. Reconciliation: every (pk, date) carries exactly one status.
  A second pass (currency mode) reads details.currency once per shortname (D-620).

ANCHOR RULES (apply mode) — settled rule set, no new rulings minted here
  D-624   cheapest ADULT/BASE per-person tier anchors "From"; child/infant/concession/add-on/gratuity
          tiers never do. Never-anchor test runs on NFKC-normalised, diacritic-folded text.
  D-625   same-customer-type tiers split by logistics are one product — cheapest base wins.
  D-631   group-size variants rank behind the entry tier.
  D-637   smallest bookable unit anchors; "per additional person" is an add-on and never anchors.
  D-639   add-on abort fires only when the ANCHOR tier itself is add-on-shaped (label, or note wording
          "per additional" / "price per item" / "extra"). Such rows are HELD and listed, never written.
  D-640/D-646  a single-tier product anchors on its sole tier (deposits excepted — D-644).
  D-614/D-635  whole-boat / party-size / party-total ladders: the FLOOR total anchors with a unit; a
          total is never divided by headcount.
  s48-R1 / D-632  per-head rate ladder whose price FALLS as the band grows: the largest band's
          per-person figure anchors.
  D-644   a deposit tier is never a price — deposit-only ladders are HELD.
  D-620   live details.currency != USD: HELD, true currency + amount stamped.
  UNSAMPLED / zero_price / probe_error: price stays null with a dated reason stamp.
  Anything else (mixed shapes the rules do not settle, no derivable unit): HELD + listed for ruling.

UNITS (_unknownFields.priceUnit, KWST vocabulary; s49–s50 derivation rules — verbatim sources only)
  per-person anchor      -> 'per person'                        (unitEvidence: tier label)
  whole-unit anchor      -> 'whole boat' [+ ' · up to N <noun>'] when label/note/product name carries a
                            vessel word; headcount + noun quoted from label, note or description
                            (unitEvidence names the source; D-632 / D-641 / D-649)
                         -> 'per jet ski' / 'per kayak' / 'per cart' / 'per bicycle' / ... for a
                            vehicle-shaped label/note/product name
                         -> 'whole rental unit' for hire/rental wording with no vessel or vehicle word
                         -> otherwise HELD (unit_underivable) — a whole-unit floor without a unit
                            repeats the D-621 defect class (D-630).

STAMPS (this repo's vocabulary, per the s50 rowfix): priceSource 's51-kwst-backfill', priceCustomerType,
  priceTierCount, priceTiers, excludedTiers, priceMinPartySize, priceVerifiedAt, priceBasis, priceUnit,
  unitEvidence, observedPriceRange (when the anchor moved across readings), probeDateValid.
  Held rows: price stays null; priceSource + priceHold + priceBasis + priceTiers + priceVerifiedAt.

usage: python3 scripts/s51-kwst-backfill.py probe|currency|apply [--dry-run]
"""
import collections, hashlib, json, re, sys, time, unicodedata, urllib.error, urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOURS = REPO / 'tours-data.json'
EV = REPO / 'data' / 's51-kwst-backfill'
SOURCE, STAMP_DAY, SITE_CUR = 's51-kwst-backfill', '2026-08-26', 'USD'
DATES = ['2026-08-29', '2026-09-05', '2026-09-19', '2026-10-10']
API = 'https://fareharbor.com/api/embed/{sn}/price-preview/per-item/v2/?item_pks={pks}&include_breakdown=yes&date={date}'
UA = 'WanderRenderMonitor/1.0 (+internal-qa)'
BATCH, SLEEP, RETRIES = 20, 1.0, 3
IMPOSSIBLE_SN = 'definitely-not-a-real-fh-shortname-zzz'
FH_RE = re.compile(r'fareharbor\.com/embeds/book/([^/?#]+)/items/(\d+)/')
EXPECT_ROWS, EXPECT_SNS = 525, 112


def u(cents): return round(cents / 100.0, 2)
def money(n): return f'${n:,.0f}' if abs(n - round(n)) < 0.005 else f'${n:,.2f}'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fold(s):
    """NFKC + strip combining marks + okina/quote folds, lower — the never-anchor test runs on this."""
    s = unicodedata.normalize('NFKC', s or '').replace('ʻ', "'").replace('’', "'").replace('‘', "'")
    return ''.join(c for c in unicodedata.normalize('NFD', s) if not unicodedata.combining(c)).lower()


# ---------------- population ----------------
def load():
    raw = TOURS.read_text(encoding='utf-8')
    doc = json.loads(raw)
    assert json.dumps(doc, indent=2, ensure_ascii=True) + '\n' == raw, 'serialization does not round-trip'
    pop = []
    for t in doc['tours']:
        if t.get('status') != 'active' or t.get('price') is not None: continue
        m = FH_RE.search(t.get('bookingUrl') or '')
        if not m: continue
        assert m.group(2) == str(t['pk']), f'bookingUrl pk mismatch on {t["pk"]}'
        t['_sn'] = m.group(1); pop.append(t)
    sns = {t['_sn'] for t in pop}
    print(f'population {len(pop)} rows / {len(sns)} shortnames', file=sys.stderr)
    assert (len(pop), len(sns)) == (EXPECT_ROWS, EXPECT_SNS), f'population drift: {len(pop)}/{len(sns)}'
    return doc, pop


# ---------------- probe ----------------
def fetch(sn, pks, day):
    url = API.format(sn=sn, pks=','.join(map(str, pks)), date=day)
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json',
                                               'Referer': f'https://fareharbor.com/embeds/book/{sn}/'})
    err = None
    for a in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read().decode('utf-8', 'replace'), None, a
        except urllib.error.HTTPError as e:
            if e.code in (400, 404): return e.code, None, f'HTTP {e.code}', a
            err = f'HTTP {e.code}'
        except Exception as e:  # noqa: BLE001
            err = str(e)[:140]
        time.sleep(SLEEP * (2 ** a))
    return None, None, err, RETRIES


def probe():
    doc, pop = load(); EV.mkdir(parents=True, exist_ok=True)
    c, _, e, _ = fetch(IMPOSSIBLE_SN, [1], DATES[0]); print('[control]', c, e, file=sys.stderr)
    if c == 200: sys.exit('FATAL: bogus shortname returned 200 — instrument is not falsifiable')
    bysn = collections.defaultdict(list)
    for t in pop: bysn[t['_sn']].append(t['pk'])
    obs = collections.defaultdict(dict); http = {}; nreq = retries = 0
    for day in DATES:
        for sn in sorted(bysn):
            pks = sorted(set(bysn[sn]))
            for j in range(0, len(pks), BATCH):
                chunk = pks[j:j + BATCH]; st, body, err, a = fetch(sn, chunk, day); nreq += 1; retries += a
                http[f'{sn}|{day}|{j}'] = st
                if err or not body or not body.lstrip().startswith('{'):
                    for pk in chunk: obs[pk][day] = {'status': 'ERROR', 'http': st, 'err': err or 'non-JSON'}
                    time.sleep(SLEEP); continue
                data = json.loads(body); seen = {int(it.get('id', -1)): it for it in data.get('items') or []}
                for pk in chunk:
                    it = seen.get(pk)
                    if it is None: obs[pk][day] = {'status': 'UNSAMPLED', 'http': st}; continue
                    av = it.get('availability') or {}; sa = av.get('start_at'); valid = bool(sa) and sa[:10] == day
                    pr = it.get('price') or {}; br = pr.get('breakdown') or {}
                    obs[pk][day] = {'status': 'OK' if valid else 'FALLBACK', 'http': st, 'start_at': sa, 'end_at': av.get('end_at'),
                                    'low': pr.get('low'), 'high': pr.get('high'), 'capacity': av.get('capacity'),
                                    'customer_types': br.get('customer_types')}
                time.sleep(SLEEP)
        print('date', day, 'done reqs', nreq, file=sys.stderr)
    miss = [(t['pk'], d) for t in pop for d in DATES if d not in obs[t['pk']]]
    assert not miss and len(obs) == len(pop), miss[:5]
    json.dump({'dates': DATES, 'probedAt': time.strftime('%Y-%m-%dT%H:%M:%S'), 'requests': nreq, 'retries': retries,
               'control': {'shortname': IMPOSSIBLE_SN, 'code': c, 'falsifiable': c != 200},
               'http': http, 'obs': {str(k): v for k, v in obs.items()}}, open(EV / 'probe.json', 'w'), indent=1)
    print('DONE', nreq, 'requests', retries, 'retries', file=sys.stderr)


def currency():
    """One request per shortname: details.currency (D-620). Item pk irrelevant — details is per company."""
    doc, pop = load(); out = {}
    for sn in sorted({t['_sn'] for t in pop}):
        pk = next(t['pk'] for t in pop if t['_sn'] == sn)
        st, body, err, _ = fetch(sn, [pk], DATES[0])
        det = (json.loads(body).get('details') or {}) if body and body.lstrip().startswith('{') else {}
        out[sn] = {'http': st, 'currency': det.get('currency'), 'includeFees': det.get('prices_include_booking_fees'),
                   'includeTaxes': det.get('prices_include_taxes'), 'err': err}
        time.sleep(SLEEP)
    json.dump(out, open(EV / 'currency.json', 'w'), indent=1)
    print(collections.Counter(v['currency'] for v in out.values()), file=sys.stderr)


# ---------------- tier classification (WENG s48 -> FST s50 lineage; D-658 amendments carried; NFKC-folded input) ----------------
NEVER = re.compile(r"\b(child|childs|child's|children|childrens|children's|kid|kids|kid's|infant|infants|baby|babies|toddler|junior|juniors|youth|youths|teen|teenager|teens|adolescent|adolescents|young adult|student|students|senior|seniors|oap|concession|concessions|pensioner|disabled|wheelchair|carer|companion|military|veteran|veterans|discount|under\s*\d+s?|\d+\s*(and|&)\s*under|family|families|add[- ]?on|extra|extras|additional|supplement|upgrade|gratuity|tip|tips|donation|deposit|voucher|gift card|redemption|per additional|spectator|non[- ]?participant|rider[- ]?along|ride[- ]?along|observer|dog|dogs|pet|pets|kit|merchandise|parking|nino|ninos|nina|ninas|bebe|infante|local|locals|resident|residents|kama'?aina|shirt|t-shirt|tee|tees|hoodie|hoodies|sweatshirt|hat|hats|cap|caps|towel|towels|koozie|apparel|merch|sticker|stickers|mug|mugs|tumbler)\b", re.I)
AGE_RANGE = re.compile(r'\b\d{1,2}\s*(-|–|to)\s*\d{1,2}\s*(yrs|years|year olds|yr olds|y/o|yo|anos)\b', re.I)
WORDNUM = r'(two|three|four|five|six|seven|eight|nine|ten|twelve|\d+)'
GROUP = re.compile(r'\b(per group|group|groups|party|parties|package|packages|bundle|private|exclusive|charter|boat|vessel|pontoon|yacht|catamaran|sailboat|vehicle|car|van|cart|table|room|cabin|pod|lane|court|couple|couples|for two|for 2|whole|hire|rental|raft|canoe|kayak|jet ?ski|waverunner|paddleboard|paddle board|sup|seater|capacity|up to \d+|' + WORDNUM + r'\s*(people|persons|ppl|pax|guests|players|riders|passengers|adults|anglers|divers))\b', re.I)
BASE_WORDS = 'adult|adults|person|per person|standard|general|guest|guests|visitor|participant|passenger|rider|player|ticket|seat|seating|admission|individual|one person|1 person|per seat|angler|diver|snorkeler|paddler|swimmer'
BASE = re.compile(r'\b(' + BASE_WORDS + r')\b', re.I)
BASE_HEAD = re.compile(r'^(' + BASE_WORDS + r')\b', re.I)
PER_PERSON = re.compile(r'\b(per (person|player|participant|head|adult|guest|rider|passenger|angler|diver|pp))\b|\beach person\b|\bpp\b|\b(1|one) (person|player)\b(?!\s*(or|to|-|–))', re.I)
ORDINAL = re.compile(r'\b(2nd|3rd|4th|5th|6th|second|third|fourth|fifth|sixth)\s+(rider|person|passenger|guest|adult|diver|angler)\b', re.I)
NOTE_NEVER = re.compile(r'^\s*extras?\s*[-–:]|\ban (optional )?extra\b|\bprice per item\b|\badd[- ]on\b|\bper additional\b|\bno flight\b|\bnon[- ]?participant\b|\bobserver\b|\bwatch only\b|\bride[- ]?along\b', re.I)
VOLUME = re.compile(r'^(' + WORDNUM + r'\s*(people|persons|adults|guests|players|passengers|anglers|divers)|groups? of|([2-9]|\d{2,})\s*(-|–|to|\+)\s*\d*\s*(people|persons|adults|guests|players|passengers|anglers))\b', re.I)
NAME_GROUP = re.compile(r'\b(hire|rental|rentals|charter|charters|private|boat|pontoon|yacht|vessel|jet ?ski|waverunner|kayak|paddleboard|sailboat|catamaran)\b', re.I)
DEPOSIT = re.compile(r'\bdeposit\b|\bdeposito\b|\bbalance due\b|\bretainer\b', re.I)
ACCESSORY = re.compile(r'\b(adaptor|adapter|boots?|gloves?|hoods?|wetsuit|cooler|dry bag|life ?jacket|fishing (pole|rod|license)|bait|ice|fuel|gas|tube|towable|anchor|umbrella|chair|cabana rental|photo|photos|video|gopro|snorkel gear|gear rental|extra person|extra participants?)\b', re.I)
AGE_CONC = re.compile(r"\b(child|children|kid|kids|infant|toddler|junior|youth|teen|senior|seniors|student|students|discount|military|veteran|veterans|local|locals|resident|residents|concession|under\s*\d+|ages?\s*\d+)", re.I)   # concession/audience siblings: the ladder is per-person (D-624 shape)
STRONG_NAME_GROUP = re.compile(r'\b(charter|charters|private boat|whole boat|private tour|boat rental|yacht|bareboat)\b', re.I)   # D-641: a product name may supply the unit only when it names the unit outright
INCREMENT = re.compile(r'\b(additional (person|people|guest|passenger|participant|angler)s?|extra (person|people|guest|passenger)s?|each additional|per additional|more than \d+|over \d+ (people|guests|passengers))\b', re.I)
ADDON = re.compile(r'per additional|\badditional\b|\bextra\b|\badd[- ]?on\b|\bsupplement\b|\bper item\b', re.I)
VEHICLE = {'jet ski': re.compile(r'\b(jet ?skis?|waverunners?|pwc)\b', re.I), 'kayak': re.compile(r'\bkayaks?\b', re.I),
           'paddleboard': re.compile(r'\b(paddle ?boards?|sup)\b', re.I), 'cart': re.compile(r'\b(golf ?carts?|carts?)\b', re.I),
           'bicycle': re.compile(r'\b(bikes?|bicycles?|e-?bikes?)\b', re.I), 'scooter': re.compile(r'\bscooters?\b', re.I),
           'canoe': re.compile(r'\bcanoes?\b', re.I), 'seabob': re.compile(r'\bseabobs?\b', re.I), 'efoil': re.compile(r'\be-?foils?\b', re.I)}
BOAT = re.compile(r'\b(charter|charters|boat|boats|pontoon|yacht|vessel|sail|sailing|sailboat|catamaran|skiff|bay boat|deck boat|cruise|airboat|fishing|offshore|inshore|sandbar|reef|wreck|anglers?|tiki|daysail|day sail|schooner|bareboat)\b', re.I)
RENTAL = re.compile(r'\b(hire|rental|rentals)\b', re.I)
HEADCOUNT = re.compile(r'\b(?:up to|max(?:imum)?(?: of)?|maximum|for|includes|seats?)\s*(\d{1,2})\s*(people|persons|ppl|pax|guests|players|riders|passengers|adults|anglers|divers|person|guest|passenger|angler|diver|seater)\b|\b(\d{1,2})\s*(people|persons|ppl|pax|guests|players|riders|passengers|adults|anglers|divers)\s*(?:max|maximum|or fewer|or less)\b|\b(\d{1,2})\s*[-–]\s*(\d{1,2})\s*(people|persons|guests|passengers|adults|anglers|divers|pax)\b', re.I)
WORD2N = {'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'twelve': 12}
NOUN_FOLD = {'persons': 'people', 'ppl': 'people', 'pax': 'people', 'person': 'people', 'guest': 'guests', 'passenger': 'passengers',
             'angler': 'anglers', 'diver': 'divers', 'seater': 'people'}


def classify(tier, ctx):
    sing = fold((tier.get('singular') or '').strip()); note = fold(tier.get('note') or ''); ctx = fold(ctx)
    if not ((tier.get('price') or 0) > 0): return 'zero'
    if DEPOSIT.search(sing) or DEPOSIT.search(note): return 'deposit'
    if NEVER.search(sing) or AGE_RANGE.search(sing): return 'never'
    if ACCESSORY.search(sing) and not ACCESSORY.search(ctx): return 'never'
    if NOTE_NEVER.search(note) or ORDINAL.search(sing): return 'never'
    if VOLUME.search(sing): return 'group'
    if BASE_HEAD.search(sing): return 'base'
    if BASE.search(sing) and not GROUP.search(sing): return 'base'
    if GROUP.search(sing): return 'group'
    if PER_PERSON.search(note): return 'base'
    if GROUP.search(note): return 'group'
    return 'variant'


def headcount(s):
    m = re.search(r'\b(' + '|'.join(WORD2N) + r')\s+(people|persons|guests|passengers|adults|anglers|divers|pax)\b', s or '', re.I)
    if m: return WORD2N[m.group(1).lower()], NOUN_FOLD.get(m.group(2).lower(), m.group(2).lower()), m.group(0)
    m = HEADCOUNT.search(s or '')
    if not m: return None
    g = m.groups()
    if g[0]: return int(g[0]), NOUN_FOLD.get(g[1].lower(), g[1].lower()), m.group(0)
    if g[2]: return int(g[2]), NOUN_FOLD.get(g[3].lower(), g[3].lower()), m.group(0)
    return int(g[5]), NOUN_FOLD.get(g[6].lower(), g[6].lower()), m.group(0)


def unit_for(label, note, product, description, siblings):
    """Whole-unit anchors only. Returns (priceUnit, unitEvidence) or (None, reason)."""
    def boat_headcount(boat_src):
        for src, txt in (('tier label', label), ('tier note', note), ('product name', product), ('description', description)):
            h = headcount(txt)
            if h: return f'whole boat · up to {h[0]} {h[1]}', f"{boat_src[0]}: '{boat_src[1].strip()[:80]}'; {src}: '{h[2]}'"
        return 'whole boat', f"{boat_src[0]}: '{boat_src[1].strip()[:80]}'"
    for src, txt in (('tier label', label), ('tier note', note)):
        if BOAT.search(txt or ''): return boat_headcount((src, txt))
    for name, rx in VEHICLE.items():
        for src, txt in (('tier label', label), ('tier note', note)):
            if rx.search(txt or ''): return f'per {name}', f"{src}: '{txt.strip()}'"
    boat_src = next(((src, txt) for src, txt in (('product name', product), ('sibling tier', siblings)) if BOAT.search(txt or '')), None)
    if boat_src: return boat_headcount(boat_src)
    for name, rx in VEHICLE.items():
        if rx.search(product or ''): return f'per {name}', f"product name: '{product.strip()}'"
    if False:
        pass
    for src, txt in (('tier label', label), ('tier note', note), ('product name', product)):
        if RENTAL.search(txt or ''): return 'whole rental unit', f"{src}: '{txt.strip()}'"
    return None, 'no vessel / vehicle / rental word in tier label, note or product name'


# ---------------- apply ----------------
def apply(dry):
    doc, pop = load()
    ev = json.load(open(EV / 'probe.json')); cur = json.load(open(EV / 'currency.json'))
    ev_sha = sha(EV / 'probe.json')[:12]
    assert ev['dates'] == DATES and ev['control']['falsifiable']
    assert set(ev['obs']) == {str(t['pk']) for t in pop}, 'probe population != current population'
    moved = sum(1 for v in ev['obs'].values() if len({r.get('start_at') for r in v.values() if r.get('start_at')}) > 1)
    assert moved > 0, 'date parameter ignored (no start_at moved)'
    before = {t['pk']: json.dumps({k: v for k, v in t.items() if k != '_sn'}, sort_keys=True) for t in doc['tours']}
    pop_pks = {t['pk'] for t in pop}
    summary, disp, holds = [], collections.Counter(), []

    for t in pop:
        v = ev['obs'][str(t['pk'])]; sn = t['_sn']
        readings = [(d, v[d]) for d in DATES]
        sampled = [(d, r) for d, r in readings if r['status'] in ('OK', 'FALLBACK')]
        errs = [r['err'] for d, r in readings if r['status'] == 'ERROR']
        x = t.setdefault('_unknownFields', {})
        rec = {'pk': t['pk'], 'sn': sn, 'name': t['name']}
        x['priceSource'] = SOURCE; x['priceVerifiedAt'] = STAMP_DAY; x['probeDates'] = DATES
        x['probeSampled'] = len(sampled); x['probeDateValid'] = sum(1 for d, r in sampled if r['status'] == 'OK')

        def hold(status, basis, tiers=None):
            x['priceHold'] = status; x['priceBasis'] = basis; x['priceTiers'] = tiers or []
            for k in ('priceUnit', 'unitEvidence', 'priceCustomerType', 'priceMinPartySize', 'excludedTiers', 'observedPriceRange'): x.pop(k, None)
            rec.update(disposition=status, basis=basis); disp[status] += 1; summary.append(rec); holds.append(rec)

        if not sampled:
            st = 'PROBE_ERROR' if len(errs) == len(DATES) else 'UNSAMPLED'
            hold(st, f'{st} ({STAMP_DAY}): absent from price-preview items[] on {len(DATES) - len(errs)}/{len(DATES)} dated probes ({", ".join(DATES)})'
                     + (f'; errors {sorted(set(errs))}' if errs else '') + '; price stays null — unsampled is never published. Evidence: probe.json sha256 ' + ev_sha)
            continue
        key = lambda r: json.dumps([[c.get('singular'), c.get('note'), c.get('price'), c.get('min_party_size')] for c in (r.get('customer_types') or [])])
        counts = collections.Counter(key(r) for d, r in sampled); maj_key = counts.most_common(1)[0][0]
        maj = next(r for d, r in sampled if key(r) == maj_key)
        valid = x['probeDateValid']
        caveat = f'{valid}/{len(sampled)} date-valid' if valid else 'evidence from next-departure echo, 0 date-valid on probe dates (D-638)'
        evid = f'{len(sampled)}/{len(DATES)} dated readings {STAMP_DAY} ({caveat}), {len(counts)} ladder shape(s), include_breakdown=yes, probe.json sha256 {ev_sha}'
        cts = maj.get('customer_types') or []
        tiers = [{'singular': c.get('singular') or '', 'note': c.get('note') or '', 'price': u(c.get('price') or 0), 'min': c.get('min_party_size'), 'id': c.get('id')} for c in cts]
        def tstr(q): return f"{q['singular']} {money(q['price'])}" + (f" ({q['note']}" + (f", min {q['min']})" if q.get('min') and q['min'] > 1 else ')') if q['note'] else (f" (min {q['min']})" if q.get('min') and q['min'] > 1 else ''))
        L = [tstr(q) for q in tiers]
        ctx = f"{t.get('name') or ''} {t.get('durationText') or ''}"
        classes = [(q, classify(q, ctx)) for q in tiers]
        variant_only = False
        if any(c == 'variant' for q, c in classes):
            grp = [q for q, c in classes if c == 'group']
            age_conc = any(c == 'never' and AGE_CONC.search(fold(q['singular'] + ' ' + q['note'])) for q, c in classes)
            if grp and all(re.search(r'\bprivate\b', fold(q['singular'])) for q in grp): inherit = 'base'   # unnamed tiers beside a "Private Charter" tier are the shared per-seat fares
            elif grp: inherit = 'group'
            elif age_conc: inherit = 'base'                                                              # a concession/age sibling makes the ladder per-person (D-624 shape)
            elif STRONG_NAME_GROUP.search(fold(t.get('name') or '')): inherit = 'group'                   # D-641: the product name names the unit outright
            else: inherit = 'variant'; variant_only = True                                              # no unit signal anywhere: HOLD for ruling, never guess
            classes = [(q, inherit if c == 'variant' else c) for q, c in classes]
        if sum(1 for q, c in classes if c == 'base') > 1:
            classes = [(q, 'never' if c == 'base' and re.fullmatch(r'rider|ride[- ]?along|passenger only|non[- ]?diver|non[- ]?snorkeler', fold(q['singular']).strip(), re.I) else c) for q, c in classes]
        rec['tiers'] = [{'singular': q['singular'], 'note': q['note'], 'price': q['price'], 'min': q['min'], 'cls': c} for q, c in classes]
        pos = [(q, c) for q, c in classes if c != 'zero']
        ladder = ' / '.join(f"{q['singular']} {money(q['price'])} [{c}]" for q, c in pos)
        if variant_only and any(c == 'variant' for q, c in pos):
            hold('variant_only', f'HELD for ruling: every priced tier is an unnamed duration/variant tier ({ladder}) and neither label, note, sibling nor an age-concession tier says per-person or whole-unit; not guessed; {evid}', L); continue
        if not pos:
            hold('zero_price', f'zero_price ({STAMP_DAY}): every live tier is $0 on the majority reading ({" / ".join(L)}); price stays null (D-575); {evid}', L); continue
        live_cur = (cur.get(sn) or {}).get('currency')
        if live_cur != SITE_CUR:
            a = min(pos, key=lambda pc: pc[0]['price'])[0]; x['liveCurrency'] = live_cur; x['liveAmount'] = a['price']
            hold(f'non_usd_currency:{live_cur}', f'HELD (D-620): live details.currency {live_cur} != site USD; true amount {live_cur} {a["price"]} ({a["singular"]}) stamped; {evid}', L); continue
        base = [q for q, c in pos if c == 'base']; group = [q for q, c in pos if c == 'group']; never = [q for q, c in pos if c == 'never']; dep = [q for q, c in pos if c == 'deposit']
        if dep and not base and not group and not never:
            hold('deposit_only', f'HELD (D-644): a deposit tier is never a price — ladder {ladder}; {evid}', L); continue
        anchor = kind = rule = None
        if len(pos) == 1 and pos[0][1] != 'deposit':
            q, c = pos[0]; anchor = q; kind = 'group' if c == 'group' else 'per-person'
            rule = 'D-640/D-646 single-tier product anchors on its sole tier' + (' (never-anchor word on the sole tier: the tier is the audience)' if c == 'never' else '')
        elif base:
            anchor = min(base, key=lambda q: q['price']); kind = 'per-person'
            rule = 'D-624 cheapest adult/base per-person tier' + (f' of {len(base)} base tiers (D-625/D-631)' if len(base) > 1 else '')
        elif group:
            hcs = [(headcount(q['singular']), q) for q in group]; hcs = [(h[0], q) for h, q in hcs if h]
            per_head = all(PER_PERSON.search(fold(q['note'])) or PER_PERSON.search(fold(q['singular'])) for q in group)
            srt = sorted(hcs, key=lambda z: z[0])
            falling = len(srt) >= 2 and all(a[0] != b[0] for a, b in zip(srt, srt[1:])) and all(b[1]['price'] < a[1]['price'] for a, b in zip(srt, srt[1:]))
            if per_head and falling:
                anchor = srt[-1][1]; kind = 'per-person'; rule = 's48-R1/D-632 per-head rate ladder (price falls as band grows): largest band per-person figure anchors'
            else:
                anchor = min(group, key=lambda q: q['price']); kind = 'group'
                rule = 'D-614/D-635 whole-unit / party-size ladder: floor total anchors (never divided by headcount)' if len(group) > 1 else 'D-614 whole-unit floor'
        else:
            hold('never_only', f'HELD for ruling: live ladder {ladder} has only never-anchor/deposit tiers and more than one of them; {evid}', L); continue
        lab, note = anchor['singular'], anchor['note']
        if ADDON.search(fold(lab)) or NOTE_NEVER.search(fold(note)) or re.search(r'per additional|per item', fold(note)):
            hold('addon_anchor', f'HELD (D-639 add-on abort): proposed anchor "{lab}" {money(anchor["price"])} (note "{note}") is add-on-shaped; ladder {ladder}; {evid}', L); continue
        if kind == 'group':
            inc = [q for q, c in pos if q is not anchor and (INCREMENT.search(fold(q['singular'])) or INCREMENT.search(fold(q['note'])))] + ([anchor] if INCREMENT.search(fold(note)) else [])
            if inc:
                hold('unit_plus_increment', f'HELD for ruling (unit+increment ladder is ambiguous — memory reference_fareharbor_unit_plus_increment_is_ambiguous): anchor "{lab}" {money(anchor["price"])} (note "{note}") with increment tier(s) {", ".join(tstr(q) for q in inc)}; ladder {ladder}; {evid}', L); continue
            if re.search(r'\bshared\b', fold(t.get('name') or '')):
                hold('shared_named_charter', f'HELD for ruling: product name says "Shared" but the anchor tier "{lab}" {money(anchor["price"])} is group-shaped; per-seat vs whole-boat undecidable from the ladder; {ladder}; {evid}', L); continue
            bare = re.search(r'\b(\d{1,2})\s*(people|persons|guests|passengers)\b', fold(lab))
            hn = headcount(note) or headcount(t.get('description') or '')
            if bare and hn and int(bare.group(1)) != hn[0]:
                hold('headcount_conflict', f'HELD for ruling: anchor label "{lab}" names {bare.group(1)} {bare.group(2)} while note/description says "{hn[2]}" — conflicting headcounts (D-649 flag); {ladder}; {evid}', L); continue
            sib = ' '.join(f"{q['singular']} {q['note']}" for q, c in pos if q is not anchor)
            unit, uev = unit_for(lab, note, t.get('name') or '', t.get('description') or '', sib)
            if not unit:
                hold('unit_underivable', f'HELD for ruling (D-630): whole-unit anchor "{lab}" {money(anchor["price"])} under {rule} but {uev}; ladder {ladder}; {evid}', L); continue
        else:
            unit, uev = 'per person', f"tier label: '{lab}'"
        same = [q['price'] for d, r in sampled for q in [{'singular': c.get('singular') or '', 'price': u(c.get('price') or 0)} for c in (r.get('customer_types') or [])]
                if q['singular'] == lab and q['price'] > 0]
        lo, hi = (min(same), max(same)) if same else (anchor['price'], anchor['price'])
        t['price'] = float(lo); t['priceLabel'] = lab; t['priceConfidence'] = 'high'
        x['priceCustomerType'] = lab; x['priceTierCount'] = len(pos); x['priceTiers'] = L
        x['excludedTiers'] = [f"{tstr(q)} [{c}]" for q, c in pos if q is not anchor]
        x['priceMinPartySize'] = anchor.get('min'); x['priceUnit'] = unit; x['unitEvidence'] = uev
        if hi > lo: x['observedPriceRange'] = [lo, hi]
        else: x.pop('observedPriceRange', None)
        x.pop('priceHold', None)
        x['priceBasis'] = (f'{SOURCE} ({STAMP_DAY}): {rule}: "{lab}" {money(lo)}' + (f' (note "{note}")' if note else '') + f', unit "{unit}" ({uev})'
                           + (f'; not anchoring: {", ".join(x["excludedTiers"])}' if x['excludedTiers'] else '')
                           + (f'; anchor varied {money(lo)}-{money(hi)} across readings (floor published)' if hi > lo else '') + f'; {evid}')
        rec.update(disposition='priced', price=t['price'], label=lab, unit=unit, rule=rule, kind=kind, range=[lo, hi] if hi > lo else None); disp['priced'] += 1; summary.append(rec)

    for t in pop: t.pop('_sn', None)
    after = {t['pk']: json.dumps(t, sort_keys=True) for t in doc['tours']}
    changed = [pk for pk in after if after[pk] != before[pk]]
    outside = [pk for pk in changed if pk not in pop_pks]
    assert not outside and len(after) == len(before), f'rows outside population changed {outside[:5]}'
    assert len(summary) == len(pop), 'attempted != succeeded'
    result = {'stampedOn': STAMP_DAY, 'population': len(pop), 'attempted': len(pop), 'succeeded': len(summary), 'rowsChanged': len(changed),
              'disposition': dict(disp), 'probeSha256': sha(EV / 'probe.json'), 'summary': summary}
    EV.mkdir(parents=True, exist_ok=True)
    json.dump(holds, open(EV / ('holds.dryrun.json' if dry else 'holds.json'), 'w'), indent=1)
    json.dump(result, open(EV / ('apply-summary.dryrun.json' if dry else 'apply-summary.json'), 'w'), indent=1)
    if not dry:
        TOURS.write_text(json.dumps(doc, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('population', 'attempted', 'succeeded', 'rowsChanged', 'disposition')}), 'DRY' if dry else 'WRITTEN')


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    if mode == 'probe': probe()
    elif mode == 'currency': currency()
    elif mode == 'apply': apply('--dry-run' in sys.argv)
    else: sys.exit('usage: probe|currency|apply [--dry-run]')
