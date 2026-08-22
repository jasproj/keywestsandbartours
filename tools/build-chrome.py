#!/usr/bin/env python3
"""
THE SINGLE DEFINITION OF THIS SITE'S HEADER AND FOOTER.

Why a generator and not a build step or JS injection
----------------------------------------------------
The site is static HTML served raw by GitHub Pages. There is no build step, and
adding one would change the deploy contract for every future edit. JS injection
was rejected outright: the header carries the primary navigation and the phone
number on a property whose traffic is organic search, and a crawler that runs no
JS would see a page with no navigation at all. The chrome therefore has to be in
the delivered bytes.

So one Python file holds the definition, writes it into all pages, and can prove
afterwards that no page has drifted from it.

    python3 tools/build-chrome.py --apply    # rewrite every page's chrome
    python3 tools/build-chrome.py --check    # exit 1 if ANY page differs

--check is the drift test. It re-renders the canonical chrome from the constants
below and compares it to what each page actually carries. Two pages cannot
diverge unless this file changes, because any divergence fails --check.
"""
import re, sys, glob, os

# ---------------------------------------------------------------- constants
SITE_NAME  = "Key West Sandbar Tours"
SITE_EMAIL = "info@keywestsandbartours.com"   # one line to change the address
SITE_PHONE_TEL  = "4074766190"
SITE_PHONE_TEXT = "(407) 476-6190"
SITE_LOGO = "/logo.png"

# CANONICAL NAV — ruled 2026-08-22. Tiki Boats, Contact, Home and FAQs removed;
# FAQs and Contact live in the footer.
NAV = [("/#tours-section", "Tours"),
       ("/#areas",         "Areas"),
       ("/blog/",          "Blog"),
       ("/about.html",     "About")]

# CANONICAL FOOTER — three columns, in this order.
# AREAS links carry NO number. The ruling allows a count rendered from
# tours-data.json OR no number; only 33 of 119 pages load app.js, and making the
# other 86 fetch a 2.9 MB catalogue to print six integers is not worth it. A
# number that cannot self-correct does not get published, so there is no number.
FOOTER_AREAS = [("/key-west.html","Key West"), ("/marathon.html","Marathon"),
                ("/key-largo.html","Key Largo"), ("/islamorada.html","Islamorada"),
                ("/stock-island.html","Stock Island"), ("/lower-keys.html","Lower Keys")]
FOOTER_POPULAR = [("/sandbar-tours.html","Sandbar Tours"), ("/sunset-cruises.html","Sunset Cruises"),
                  ("/snorkeling-tours.html","Snorkeling Tours"), ("/dolphin-tours.html","Dolphin Tours"),
                  ("/private-charters.html","Private Charters"), ("/tiki-boats-key-west.html","Tiki Boats")]
FOOTER_COMPANY = [("/about.html","About"), ("/faq.html","FAQs"),
                  ("/contact.html","Contact"), ("/advertise.html","Advertise")]

CSS_HREF = "/chrome.css"
JS_SRC   = "/chrome.js"

# ---------------------------------------------------------------- rendering
def _links(items, cls=""):
    c = f' class="{cls}"' if cls else ""
    return "\n".join(f'        <li><a{c} href="{h}">{t}</a></li>' for h, t in items)

def header_html():
    nav = "\n".join(f'        <a href="{h}">{t}</a>' for h, t in NAV)
    mob = "\n".join(f'      <a href="{h}">{t}</a>' for h, t in NAV)
    return f'''<header class="site-header">
    <div class="site-header-inner">
      <a href="/" class="site-logo">
        <img src="{SITE_LOGO}" alt="{SITE_NAME}" width="40" height="40">
        <span class="site-logo-text">{SITE_NAME}</span>
      </a>
      <nav class="site-nav" aria-label="Main navigation">
{nav}
      </nav>
      <a class="site-phone" href="tel:{SITE_PHONE_TEL}">
        <span class="site-phone-icon" aria-hidden="true">&#128222;</span>
        <span class="site-phone-number">{SITE_PHONE_TEXT}</span>
      </a>
      <button class="site-nav-toggle" type="button" aria-label="Menu" aria-expanded="false" aria-controls="site-nav-mobile">&#9776;</button>
    </div>
    <nav class="site-nav-mobile" id="site-nav-mobile" aria-label="Mobile navigation">
{mob}
    </nav>
  </header>'''

def footer_html():
    return f'''<footer class="site-footer">
    <div class="site-footer-inner">
      <div class="site-footer-col">
        <h4>Areas</h4>
        <ul>
{_links(FOOTER_AREAS)}
        </ul>
      </div>
      <div class="site-footer-col">
        <h4>Popular</h4>
        <ul>
{_links(FOOTER_POPULAR)}
        </ul>
      </div>
      <div class="site-footer-col">
        <h4>Company</h4>
        <ul>
{_links(FOOTER_COMPANY)}
          <li><a href="mailto:{SITE_EMAIL}">{SITE_EMAIL}</a></li>
        </ul>
      </div>
    </div>
    <div class="site-footer-legal">
      <p>&copy; 2026 {SITE_NAME}. Book direct with local operators.</p>
    </div>
  </footer>'''

# ---------------------------------------------------------------- rewriting
HEADER_RE = re.compile(r'<header\b.*?</header>', re.S)
FOOTER_RE = re.compile(r'<footer\b.*?</footer>', re.S)

def transform(t):
    """Return the page with canonical chrome, asset links and a single email."""
    h, f = header_html(), footer_html()
    # header: replace an existing one, else insert immediately after <body ...>
    if HEADER_RE.search(t):
        t = HEADER_RE.sub(lambda m: h, t, count=1)
    else:
        t = re.sub(r'(<body[^>]*>)', lambda m: m.group(1) + "\n  " + h, t, count=1)
    # footer: replace an existing one, else insert just before </body>
    if FOOTER_RE.search(t):
        t = FOOTER_RE.sub(lambda m: f, t, count=1)
    else:
        t = t.replace('</body>', "  " + f + "\n</body>", 1)
    # chrome stylesheet + script, exactly once each
    if CSS_HREF not in t:
        t = t.replace('</head>', f'  <link rel="stylesheet" href="{CSS_HREF}">\n</head>', 1)
    if JS_SRC not in t:
        t = t.replace('</body>', f'  <script src="{JS_SRC}" defer></script>\n</body>', 1)
    # one contact address, everywhere it is used as THIS SITE's address
    t = t.replace("walktheplankadventures@gmail.com", SITE_EMAIL)
    return t

def pages():
    return sorted(p for p in glob.glob('**/*.html', recursive=True)
                  if not p.startswith('node_modules'))

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--check'
    drift = []
    for p in pages():
        src = open(p, encoding='utf-8').read()
        out = transform(src)
        if mode == '--apply':
            if out != src:
                open(p, 'w', encoding='utf-8').write(out)
        else:
            if out != src:
                drift.append(p)
    if mode == '--apply':
        print(f"applied canonical chrome to {len(pages())} pages")
        return 0
    if drift:
        print(f"CHROME DRIFT: {len(drift)} page(s) differ from the single definition")
        for p in drift[:20]:
            print("   ", p)
        return 1
    print(f"chrome OK: {len(pages())} pages match the single definition")
    return 0

if __name__ == '__main__':
    sys.exit(main())
