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

Capt. Dane's own photography, confirmed by Jason 2026-07-28. Copied from the `wtpa`
repository; copying between `keywestsandbartours` and `wtpa` is intra-entity (both WTPA LLC)
and permitted. **These must never be copied to a Claduta-owned site.**

Renamed `.jpg` → `.webp` on copy: the source files were WebP carrying a `.jpg` extension.
Fixed at the point of copy rather than inheriting a known defect.

| File | Dimensions | Subject (verified by viewing) |
|---|---|---|
| `images/keys/dane_drone.webp` | 2000×1125 | Aerial: pontoon boat anchored on a shallow turquoise sandbar, one person wading |
| `images/keys/sharks_drone.webp` | 2000×1125 | Aerial: two nurse sharks over shallow flats, pontoon in background |
| `images/keys/shark_drone_2.webp` | 2000×1125 | Aerial: pontoon anchored, one nurse shark below |

`Dane_Spear_3.jpg` (828×819, Capt. Dane spearfishing) is also confirmed ORIGINAL but is **not
used**: the only page it fits — `blog/offshore-vs-backcountry-fishing.html` — carries its image
in a full-bleed `div.blog-hero` measured at 1440×1281, which would upscale it ~1.7×. Card slots
only. See the sourcing list below.

## LICENSED / FREE — Pexels

All sourced from [Pexels](https://www.pexels.com) under the [Pexels License](https://www.pexels.com/license/)
on 2026-07-28. Accepted **only** where the photographer's own URL slug names a Florida Keys
place — query relevance is not provenance, and Pexels `alt` text is auto-generated and was not
trusted. Resized to 1600px wide, `cwebp -q 82`.

| File | Photographer | Source slug | Original |
|---|---|---|---|
| `images/keys/a-house-with-palm-trees-on-the-front-in-key.webp` | Arian Fernandez | [`a-house-with-palm-trees-on-the-front-in-key-west-florida-usa-18326885`](https://www.pexels.com/photo/a-house-with-palm-trees-on-the-front-in-key-west-florida-usa-18326885/) | 6143x3632 |
| `images/keys/a-seaplane-at-fort-jefferson-in-the-dry-tort.webp` | Colon Freld | [`a-seaplane-at-fort-jefferson-in-the-dry-tortugas-in-key-west-florida-united-states-12902831`](https://www.pexels.com/photo/a-seaplane-at-fort-jefferson-in-the-dry-tortugas-in-key-west-florida-united-states-12902831/) | 4016x3012 |
| `images/keys/aerial-shot-of-the-key-west-lighthouse-in-fl.webp` | Mikhail Nilov | [`aerial-shot-of-the-key-west-lighthouse-in-florida-9400886`](https://www.pexels.com/photo/aerial-shot-of-the-key-west-lighthouse-in-florida-9400886/) | 5464x3640 |
| `images/keys/aerial-view-of-the-seven-mile-bridge-above-t.webp` | Mikhail Nilov | [`aerial-view-of-the-seven-mile-bridge-above-the-sea-9400885`](https://www.pexels.com/photo/aerial-view-of-the-seven-mile-bridge-above-the-sea-9400885/) | 5464x3640 |
| `images/keys/lonely-palm-tree-on-key-west-beach.webp` | DΛVΞ GΛRCIΛ | [`lonely-palm-tree-on-key-west-beach-35712229`](https://www.pexels.com/photo/lonely-palm-tree-on-key-west-beach-35712229/) | 6000x4000 |
| `images/keys/solitary-palm-tree-on-key-west-beach.webp` | DΛVΞ GΛRCIΛ | [`solitary-palm-tree-on-key-west-beach-35712231`](https://www.pexels.com/photo/solitary-palm-tree-on-key-west-beach-35712231/) | 6000x4000 |
| `images/keys/stunning-ocean-view-at-florida-keys-bridge.webp` | Dominik Gryzbon | [`stunning-ocean-view-at-florida-keys-bridge-31546925`](https://www.pexels.com/photo/stunning-ocean-view-at-florida-keys-bridge-31546925/) | 6016x4016 |
| `images/keys/tropical-palm-sunset-in-key-west.webp` | Anatolii Grytsenko | [`tropical-palm-sunset-in-key-west-30912992`](https://www.pexels.com/photo/tropical-palm-sunset-in-key-west-30912992/) | 4315x5394 |
| `images/keys/tropical-palm-trees-and-tiki-hut-in-islamora.webp` | Sheree Bagensie | [`tropical-palm-trees-and-tiki-hut-in-islamorada-36827874`](https://www.pexels.com/photo/tropical-palm-trees-and-tiki-hut-in-islamorada-36827874/) | 2825x3948 |
| `images/keys/ancient-dry-tortugas-national-park-in-florid.webp` | Colon Freld | [`ancient-dry-tortugas-national-park-in-florida-12902484`](https://www.pexels.com/photo/ancient-dry-tortugas-national-park-in-florida-12902484/) | 3971x2978 |
| `images/keys/building-of-key-west-shipwreck-museum.webp` | PeopleByOwen | [`building-of-key-west-shipwreck-museum-15822391`](https://www.pexels.com/photo/building-of-key-west-shipwreck-museum-15822391/) | 4345x6518 |
| `images/keys/charming-historic-houses-in-key-west-florida.webp` | Dominik Gryzbon | [`charming-historic-houses-in-key-west-florida-31546926`](https://www.pexels.com/photo/charming-historic-houses-in-key-west-florida-31546926/) | 6016x4016 |
| `images/keys/charming-key-west-shell-warehouse-exterior-d.webp` | Stanley  Louigene | [`charming-key-west-shell-warehouse-exterior-display-33664868`](https://www.pexels.com/photo/charming-key-west-shell-warehouse-exterior-display-33664868/) | 3024x4032 |
| `images/keys/charming-key-west-street-with-festive-decora.webp` | Dominik Gryzbon | [`charming-key-west-street-with-festive-decorations-31546935`](https://www.pexels.com/photo/charming-key-west-street-with-festive-decorations-31546935/) | 5712x3747 |
| `images/keys/colorful-signpost-in-florida-keys-cafe.webp` | Sarah O'Shea | [`colorful-signpost-in-florida-keys-cafe-33248591`](https://www.pexels.com/photo/colorful-signpost-in-florida-keys-cafe-33248591/) | 3024x4032 |
| `images/keys/conch-tour-train-in-key-west-florida-usa.webp` | Arian Fernandez | [`conch-tour-train-in-key-west-florida-usa-18326933`](https://www.pexels.com/photo/conch-tour-train-in-key-west-florida-usa-18326933/) | 6240x3958 |
| `images/keys/fort-jefferson-in-the-dry-tortugas-national.webp` | Charles Shepherd | [`fort-jefferson-in-the-dry-tortugas-national-park-florida-usa-14345243`](https://www.pexels.com/photo/fort-jefferson-in-the-dry-tortugas-national-park-florida-usa-14345243/) | 4000x3000 |
| `images/keys/historic-trolley-in-key-west-florida.webp` | Stanley  Louigene | [`historic-trolley-in-key-west-florida-33664873`](https://www.pexels.com/photo/historic-trolley-in-key-west-florida-33664873/) | 3024x4032 |
| `images/keys/iconic-mile-0-sign-in-key-west-florida.webp` | Matheus Bertelli | [`iconic-mile-0-sign-in-key-west-florida-37774962`](https://www.pexels.com/photo/iconic-mile-0-sign-in-key-west-florida-37774962/) | 4032x6048 |
| `images/keys/key-west-directional-road-sign-on-sunny-day.webp` | Matheus Bertelli | [`key-west-directional-road-sign-on-sunny-day-37774954`](https://www.pexels.com/photo/key-west-directional-road-sign-on-sunny-day-37774954/) | 6048x4032 |
| `images/keys/key-west-orange-trolley-on-a-rainy-day.webp` | Stanley  Louigene | [`key-west-orange-trolley-on-a-rainy-day-33664871`](https://www.pexels.com/photo/key-west-orange-trolley-on-a-rainy-day-33664871/) | 3024x4032 |
| `images/keys/vacation-homes-of-parrot-key-hotel-and-villa.webp` | Mikhail Nilov | [`vacation-homes-of-parrot-key-hotel-and-villas-in-key-west-florida-9400887`](https://www.pexels.com/photo/vacation-homes-of-parrot-key-hotel-and-villas-in-key-west-florida-9400887/) | 5464x3640 |

## ⚠️ Sourcing list — pages deliberately LEFT with a wrong image

No verified asset fits these pages. A merely-plausible substitute is how a photo of Utah and a
photo of Malaysia reached this network, so the wrong image is left in place and recorded here
instead.

| Page | Currently shows | What it needs |
|---|---|---|
| `blog/kayaking-key-west-mangroves.html` | a breaking ocean wave | a Keys kayak / mangrove-tunnel photograph — none exists in any pool |
| `blog/offshore-vs-backcountry-fishing.html` | underwater scuba divers (full-bleed hero, 1440×1281) | a Keys fishing photograph at hero resolution; `Dane_Spear_3.jpg` is the right subject but only 828×819 |

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

