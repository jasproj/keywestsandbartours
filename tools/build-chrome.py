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

--check runs two independent tests and fails if either fails:

  1. DRIFT -- it re-renders the canonical chrome from the constants below and
     compares it to what each page actually carries. Two pages cannot diverge
     unless this file changes, because any divergence fails --check.
  2. LINK TARGETS -- every site-absolute href in the canonical nav and footer
     must resolve to a file that exists.

Test 2 exists because test 1 structurally cannot catch a bad canonical link:
the canon is the thing every page is compared against, so a link to a file that
has never existed matches on all 119 pages and passes clean. #227 shipped
exactly that -- a footer link to /snorkeling-tours.html, a path with no blob on
any ref -- and it 404'd on every page until #233 repointed it at /snorkeling.html.
"""
import re, sys, glob, os

# ---------------------------------------------------------------- constants
SITE_NAME  = "Key West Sandbar Tours"
SITE_EMAIL = "walktheplankadventures@gmail.com"   # one line to change the address
# Addresses this site has published before. Any of these found in a page is
# rewritten to SITE_EMAIL, so retiring an address is adding it to this list.
# NOTE: an address goes here only once it is confirmed to RECEIVE mail.
# info@keywestsandbartours.com was published across 119 pages by #227 and
# does not exist -- no mail service is configured on the domain.
LEGACY_EMAILS = ["info@keywestsandbartours.com"]
SITE_PHONE_TEL  = "4074766190"
SITE_PHONE_TEXT = "(407) 476-6190"
SITE_LOGO = "/images/header-logo.png"

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
                  ("/snorkeling.html","Snorkeling Tours"), ("/dolphin-tours.html","Dolphin Tours"),
                  ("/private-charters.html","Private Charters"), ("/tiki-boats-key-west.html","Tiki Boats")]
FOOTER_COMPANY = [("/about.html","About"), ("/faq.html","FAQs"),
                  ("/contact.html","Contact"), ("/advertise.html","Advertise")]

CSS_HREF = "/chrome.css"
JS_SRC   = "/chrome.js"

# ------------------------------------------------------------ link targets
# The canonical link sets whose "/..." hrefs must point at real files.
LINK_SETS = [("NAV", NAV), ("FOOTER_AREAS", FOOTER_AREAS),
             ("FOOTER_POPULAR", FOOTER_POPULAR), ("FOOTER_COMPANY", FOOTER_COMPANY)]

def resolve_target(href):
    """Map a site-absolute href to the repo file it serves, or None if missing.

    Mirrors how GitHub Pages serves this site: "/" and "/dir/" serve index.html,
    and an extensionless path may be served by "<path>.html". Fragments and
    query strings are not part of the file lookup.
    """
    path = href.split("#", 1)[0].split("?", 1)[0]
    if not path.startswith("/"):
        return None
    rel = path.lstrip("/")
    if rel == "" or rel.endswith("/"):
        rel += "index.html"
    for cand in (rel, rel + ".html", os.path.join(rel, "index.html")):
        if os.path.isfile(cand):
            return cand
    return None

def missing_targets():
    """Every canonical nav/footer href that resolves to nothing in the tree."""
    out = []
    for name, items in LINK_SETS:
        for href, label in items:
            if href.startswith("/") and resolve_target(href) is None:
                out.append((name, href, label))
    return out

def canonical_hrefs():
    return [h for _, items in LINK_SETS for h, _ in items if h.startswith("/")]

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
        <picture><source type="image/webp" srcset="/images/header-logo-160.webp 160w, /images/header-logo-320.webp 320w, /images/header-logo-480.webp 480w" sizes="(max-width: 860px) 93px, 103px"><img src="{SITE_LOGO}" alt="{SITE_NAME}" loading="eager" decoding="async"></picture>
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
    <div class="site-footer-brand">
      <a href="/"><img src="/images/header-logo.png" alt="{SITE_NAME}" class="site-footer-logo"></a>
      <p>Book direct with local operators.</p>
    </div>
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
          <li><a href="mailto:{SITE_EMAIL}">Email Us</a></li>
        </ul>
      </div>
    </div>
    <div class="site-footer-network">
      <h4>Wander Network</h4>
      <ul>
        <li><a href="https://floridasandbartours.com" target="_blank" rel="noopener">Florida Sandbar Tours</a></li>
        <li><a href="https://wanderpuertorico.com" target="_blank" rel="noopener">Wander Puerto Rico</a></li>
        <li><a href="https://wanderhawaii.com" target="_blank" rel="noopener">Wander Hawaii</a></li>
        <li><a href="https://wanderusvi.com" target="_blank" rel="noopener">Wander USVI</a></li>
        <li><a href="https://wanderamsterdam.com" target="_blank" rel="noopener">Wander Amsterdam</a></li>
        <li><a href="https://wanderengland.com" target="_blank" rel="noopener">Wander England</a></li>
        <li><a href="https://wandernewzealand.com" target="_blank" rel="noopener">Wander New Zealand</a></li>
      </ul>
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
    for legacy in LEGACY_EMAILS:
        t = t.replace(legacy, SITE_EMAIL)
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
    rc = 0
    if drift:
        print(f"CHROME DRIFT: {len(drift)} page(s) differ from the single definition")
        for p in drift[:20]:
            print("   ", p)
        rc = 1
    else:
        print(f"chrome OK: {len(pages())} pages match the single definition")
    missing = missing_targets()
    if missing:
        print(f"DEAD CANONICAL LINK: {len(missing)} nav/footer target(s) do not exist")
        for name, href, label in missing:
            print(f"    {name}: {href}  ({label}) -> no file in tree")
        rc = 1
    else:
        print(f"link targets OK: {len(canonical_hrefs())} nav/footer hrefs resolve")
    return rc

if __name__ == '__main__':
    sys.exit(main())
