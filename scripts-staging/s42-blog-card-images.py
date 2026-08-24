#!/usr/bin/env python3
"""ONE-SHOT (s42, 2026-08-24): add card art to hand-authored .tour-card-blog cards.

These cards have no generator — blog/ is passed through verbatim by Jekyll
(theme: null, keep_files: [blog], 0 pages with front matter), and the markup
arrived via bulk "Add N blog posts" commits. So this script edits the pages in
place, deterministically, rather than regenerating them.

Rules (adjudicated 2026-08-24):
  src      = tours-data.json `image`, else galleryImages[0], else NO <img> at all
  transform= resize=w:640,fit:max/auto_image/compress/  (2x the 320px CSS slot)
  host     = all handles normalised onto cdn.filestackcontent.com; 7 rows carry
             legacy www.filepicker.io URLs whose handles serve fine from the CDN
  markup   = byte-exact match of the 8-page precedent (lazy/async/onerror-hide)
  CSS      = add the precedent `.tour-card-blog img` rule where absent.
             Accent-colour consolidation deliberately NOT done - see report.

Idempotent: a card that already contains an <img> is skipped.
"""
import json, os, re, sys, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TX   = "resize=w:640,fit:max/auto_image/compress/"
CDN  = "https://cdn.filestackcontent.com/"
CSS_RULE = ("        .tour-card-blog img { display: block; width: 100%; max-width: 320px; "
            "height: 180px; object-fit: cover; border-radius: 8px; margin: 0 0 14px; "
            "background: #dfe6ec; }\n")

tours = json.load(open(os.path.join(ROOT, "tours-data.json"), encoding="utf-8"))["tours"]
BY = {str(t["pk"]): t for t in tours}

def src_for(pk):
    """Canonical transformed CDN url for a pk, or None if it has no art at all."""
    t = BY.get(pk) or {}
    raw = (t.get("image") or "").strip()
    if not raw:
        gal = t.get("galleryImages") or []
        raw = (gal[0] if gal else "").strip()
    if not raw:
        return None
    handle = raw.rstrip("/").rsplit("/", 1)[-1]        # works for cdn.* and filepicker.io
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,}", handle):
        return None
    return CDN + TX + handle

CARD_OPEN = '<div class="tour-card-blog">'

TAG = re.compile(r"<(/?)div\b", re.I)

def card_end(s, start):
    """Index just past the </div> that closes the card at `start`.

    A naive s.find("</div>") truncates any card containing a nested div - on
    this site that is the .sponsor-slot injected mid-card, which hid 5 cards'
    booking anchors from the first run of this script.
    """
    depth = 0
    for m in TAG.finditer(s, start):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return s.find(">", m.end()) + 1
    return len(s)

def process(path):
    s = open(path, encoding="utf-8").read()
    orig = s
    added = skipped = noart = 0
    out, i = [], 0
    while True:
        j = s.find(CARD_OPEN, i)
        if j < 0:
            out.append(s[i:]); break
        end = card_end(s, j)
        block = s[j:end]
        out.append(s[i:j]); out.append(CARD_OPEN)
        rest = block[len(CARD_OPEN):]
        m = re.search(r'data-tour-id="(\d+)"', rest)
        if "<img" in rest or not m:
            skipped += 1
        else:
            pk = m.group(1)
            url = src_for(pk)
            if url is None:
                noart += 1                              # no element at all
            else:
                name = (BY.get(pk) or {}).get("name") or "Key West tour"
                alt = html.escape(name, quote=True)
                img = ('\n                <img src="%s" alt="%s" loading="lazy" '
                       'decoding="async" onerror="this.style.display=&quot;none&quot;">'
                       % (url, alt))
                rest = img + rest
                added += 1
        out.append(rest)
        i = end
    s = "".join(out)

    # ensure the precedent CSS rule exists on this page
    if added and ".tour-card-blog img" not in s:
        m = re.search(r"^([ \t]*)\.tour-card-blog \{[^\n]*\n", s, re.M)
        if m:
            s = s[:m.end()] + CSS_RULE + s[m.end():]
        else:
            # No inline .tour-card-blog block on this page (1 page: it relies on
            # styles.css, which sizes nothing). Without a rule the new <img>
            # would render at natural size, so append into the page's <style>.
            m2 = re.search(r"\n([ \t]*)</style>", s)
            if m2:
                s = s[:m2.start()] + "\n" + CSS_RULE.rstrip("\n") + s[m2.start():]
            else:
                sys.stderr.write("  !! no <style> block: %s\n" % os.path.basename(path))
    if s != orig:
        open(path, "w", encoding="utf-8").write(s)
    return added, skipped, noart, s != orig

if __name__ == "__main__":
    targets = sorted(
        os.path.join(ROOT, "blog", f) for f in os.listdir(os.path.join(ROOT, "blog"))
        if f.endswith(".html"))
    tot_a = tot_s = tot_n = 0; touched = 0
    for p in targets:
        a, sk, n, ch = process(p)
        tot_a += a; tot_s += sk; tot_n += n; touched += ch
        if a or n:
            print(f"  {os.path.relpath(p, ROOT):52} +{a:>2} img  {n} no-art  ({sk} already had one)")
    print(f"\npages modified: {touched}   images added: {tot_a}   cards left imageless: {tot_n}   skipped(existing img): {tot_s}")
