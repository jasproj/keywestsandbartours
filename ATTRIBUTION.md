# Image Provenance — keywestsandbartours

This repository previously had **no attribution or credits file of any kind**. This baseline
was created 2026-07-28 during a network image audit. It records what is *evidenced*, not what
is assumed.

Three categories are used. **A category is only asserted where evidence supports it.**

- **ORIGINAL** — Jason's or Capt. Dane's own photography. Asserted only for files Jason has
  explicitly confirmed. Not inferred from metadata: an Apple or Samsung ICC profile appears in
  every photo those devices take, including photos taken by someone else, and is not evidence
  of ownership.
- **LICENSED / FREE** — a recorded licence and source exists (Pexels, Pixabay, Wikimedia, etc.).
- **UNKNOWN** — provenance not established. **This is the default.** It does not imply the file
  is unlicensed; it means no record exists and none should be invented.

## Method notes

EXIF is weak evidence here in both directions. Many files were converted to WebP, and that
conversion **strips EXIF entirely** — so "no metadata" means the pipeline erased it, not that
the image is unattributed.

Adobe XMP namespace URIs (`adobe:ns:meta/`, `http://ns.adobe.com/xap/1.0/`) appear in almost any
file touched by XMP-aware software and are **not** stock provenance. Genuine stock provenance
looks like an explicit `<pur:creditLine>` or `<dc:rights>` naming a vendor or rights holder —
which is how `dolphins2.jpeg` (Adobe Stock, "Copyright: Eugene Sergeev") was identified and
removed in PR #73.

## ORIGINAL — confirmed by Jason

Capt. Dane's own photography. Held in the `wtpa` repository; copying between `keywestsandbartours`
and `wtpa` is intra-entity (both WTPA LLC) and permitted. **These must never be copied to a
Claduta-owned site.**

| File | Subject | Evidence |
|---|---|---|
| `dane_drone.jpg` | Aerial: pontoon anchored on a shallow turquoise sandbar, one person wading | Confirmed by Jason; drone frame, consistent single shoot |
| `sharks_drone.jpg` | Aerial: two nurse sharks over shallow flats, pontoon in background | Confirmed by Jason; same shoot |
| `shark_drone_2.jpg` | Aerial: pontoon anchored, one nurse shark below | Confirmed by Jason; same shoot |
| `Dane_Spear_3.jpg` | Capt. Dane, spearfishing | Confirmed by Jason; named subject |

*(Arriving in this repo with the image-swap work; listed here so the category is defined.)*

## LICENSED / FREE

*(none recorded yet)*

## UNKNOWN — default for every file currently in this repository

No licence or source record exists for any of the following. Listed for completeness; several
are strong candidates for the unfilled ad slots and are retained deliberately.

| File | Dimensions | Actual format | Bytes | Referenced |
|---|---|---|---:|---:|
| `3hr_chillout.webp` | 1000×750 | WebP | 42,046 | 0 |
| `4_hour_private_snorkel.webp` | 723×273 | WebP | 28,126 | 0 |
| `KWST_Freediver.png` | 1536×1024 | WebP ⚠️ ext/format mismatch | 332,746 | 0 |
| `Pink_LadiesED.webp` | 720×960 | WebP | 126,114 | 1 |
| `apple-touch-icon.png` | 180×180 | PNG | 75,682 | 4 |
| `big-pine-key-image.jpg` | 600×399 | JPEG | 26,683 | 1 |
| `blog-best-time.jpg` | 600×800 | JPEG | 114,067 | 1 |
| `blog-dry-tortugas.jpg` | 600×398 | JPEG | 62,596 | 1 |
| `blog-fishing-license.jpg` | 800×600 | JPEG | 84,810 | 1 |
| `blog-fishing.jpg` | 600×307 | JPEG | 42,559 | 1 |
| `blog-hemingway.jpg` | 600×398 | JPEG | 91,326 | 1 |
| `blog-hero-bg.jpg` | 1200×900 | JPEG | 113,423 | 1 |
| `blog-iguana.jpg` | 600×689 | JPEG | 129,589 | 1 |
| `blog-jetski.jpg` | 600×400 | JPEG | 62,847 | 1 |
| `blog-lobster.jpg` | 600×450 | JPEG | 66,994 | 1 |
| `blog-rooster.jpg` | 600×400 | JPEG | 39,282 | 1 |
| `blog-sandbar.jpg` | 600×450 | JPEG | 51,606 | 1 |
| `blog-spearfishing.jpg` | 600×399 | JPEG | 51,326 | 1 |
| `blog-sunset-cruises.jpg` | 600×450 | JPEG | 43,326 | 1 |
| `blog-things-to-do.jpg` | 600×412 | JPEG | 105,017 | 1 |
| `center_console_rental.webp` | 1800×1530 | WebP | 411,956 | 0 |
| `favicon-16.png` | 16×16 | PNG | 1,219 | 12 |
| `favicon-32.png` | 32×32 | PNG | 3,369 | 67 |
| `guide-bg.jpg` | 2000×1500 | WebP ⚠️ ext/format mismatch | 444,280 | 0 |
| `hero-bg.jpg` | 1200×1600 | JPEG | 229,263 | 2 |
| `hero-poster.png` | 1536×1024 | WebP ⚠️ ext/format mismatch | 233,350 | 3 |
| `images/hero-photo-1.jpg` | 2400×1602 | JPEG | 929,333 | 1 |
| `images/hero-photo-2.jpg` | 2400×1602 | JPEG | 1,282,815 | 1 |
| `images/hero-photo-3.jpg` | 2400×1600 | JPEG | 657,969 | 1 |
| `images/hero-photo-4.jpg` | 2400×1800 | JPEG | 1,124,185 | 1 |
| `islamorada-hero.jpg` | 1400×788 | JPEG | 296,631 | 1 |
| `key-largo-hero.jpg` | 1400×788 | JPEG | 125,366 | 1 |
| `key-largo-image.jpg` | 600×420 | JPEG | 48,905 | 1 |
| `key-west-area.jpg` | 1000×1333 | JPEG | 358,988 | 0 |
| `key-west-hero.jpg` | 1400×1050 | JPEG | 226,871 | 1 |
| `logo.png` | 350×360 | PNG | 40,897 | 150 |
| `logo.webp` | 350×360 | WebP | 45,410 | 4 |
| `lower-keys-hero.jpg` | 1400×1049 | JPEG | 104,406 | 1 |
| `luxury-charter-hero.png` | 1536×1024 | WebP ⚠️ ext/format mismatch | 233,350 | 0 |
| `marathon-hero.jpg` | 1400×1050 | JPEG | 209,783 | 1 |
| `og-bachelorette-party-boats.png` | 1200×630 | PNG | 1,046,730 | 2 |
| `og-image.jpg` | 1200×630 | JPEG | 330,428 | 20 |
| `og-private-boat-charters.png` | 1200×630 | PNG | 948,150 | 3 |
| `og-private-sandbar-charters.png` | 1200×630 | PNG | 877,332 | 3 |
| `og-sunset-cruises.png` | 1536×1024 | WebP ⚠️ ext/format mismatch | 233,350 | 0 |
| `og-tiki-boats-key-west.jpg` | 1200×630 | JPEG | 199,635 | 4 |
| `private_harbor.webp` | 960×720 | WebP | 73,536 | 0 |
| `private_patch.webp` | 1024×683 | WebP | 89,962 | 0 |
| `private_romantic.webp` | 768×432 | WebP | 27,318 | 0 |
| `pufferfish-square.png` | 420×399 | PNG | 283,340 | 0 |
| `salty_soul.webp` | 1000×750 | WebP | 67,176 | 0 |
| `sandbar-couple.jpg` | 2000×1500 | WebP ⚠️ ext/format mismatch | 144,316 | 0 |
| `sandbar-floating.jpg` | 1000×1333 | JPEG | 358,988 | 0 |
| `sandbar-mangroves.jpg` | 2000×1500 | WebP ⚠️ ext/format mismatch | 381,994 | 0 |
| `sandbar-wide.jpg` | 1000×750 | JPEG | 222,331 | 0 |
| `second_proposal.webp` | 1000×993 | WebP | 100,252 | 0 |
| `snorkelers1.webp` | 1000×750 | WebP | 105,876 | 1 |
| `southernmost-point.jpg` | 600×400 | JPEG | 58,834 | 1 |
| `stock-island-hero.jpg` | 1400×788 | JPEG | 228,986 | 1 |
| `sunset_cruise_near_me.webp` | 1000×664 | WebP | 31,548 | 0 |
| `sushi.webp` | 1000×526 | WebP | 68,866 | 0 |
| `thank-you-bg.jpeg` | 1500×2000 | JPEG | 441,157 | 1 |
| `ultimate_private.webp` | 1333×2000 | WebP | 314,622 | 0 |

### Known quirk: extension / format mismatches

Several files carry an extension that disagrees with their actual bytes (`.jpg` or `.png` files
that are really WebP). Browsers sniff content so nothing renders incorrectly, but any tooling
that keys on file extension (`cwebp`, `sips`, build scripts) will misbehave. Logged, not changed.

