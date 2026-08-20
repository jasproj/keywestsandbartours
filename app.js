// Key West Sandbar Tours - App.js
// Tour rendering, filtering, and click tracking

// Fallback for tour records with no image. Applied at render time, not just via
// onerror: `src="undefined"` costs a real 404 before onerror can rescue it.
// Local + ORIGINAL Capt. Dane photography, recorded in ATTRIBUTION.md.
const FALLBACK_IMAGE = '/images/keys/dane_drone.webp';

let allTours = [];

// Wire the homepage "Verified Tours" stat to the live (non-dead) catalog
// size, replacing the hardcoded value. No-op on pages without the element.
function updateVerifiedToursCount(n) {
    const el = document.getElementById('verified-tours-count');
    if (el) el.textContent = Number(n).toLocaleString();
}
let filteredTours = [];
let displayedCount = 0;
const TOURS_PER_PAGE = 24;

// Fisher-Yates shuffle (non-mutating — returns a shuffled copy)
function shuffleArray(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// Area mapping
function getArea(location) {
    const loc = (location || '').toLowerCase();
    if (loc.includes('key west')) return 'key-west';
    if (loc.includes('stock island')) return 'stock-island';
    if (loc.includes('marathon') || loc.includes('key colony')) return 'marathon';
    if (loc.includes('key largo')) return 'key-largo';
    if (loc.includes('islamorada')) return 'islamorada';
    if (loc.includes('tavernier')) return 'tavernier';
    // Lower Keys: Big Pine, Little Torch, Summerland, Big Coppitt, Duck Key
    return 'lower-keys';
}

function getAreaName(location) {
    const loc = (location || '').toLowerCase();
    if (loc.includes('key west')) return 'Key West';
    if (loc.includes('stock island')) return 'Stock Island';
    if (loc.includes('marathon')) return 'Marathon';
    if (loc.includes('key colony')) return 'Key Colony Beach';
    if (loc.includes('key largo')) return 'Key Largo';
    if (loc.includes('islamorada')) return 'Islamorada';
    if (loc.includes('tavernier')) return 'Tavernier';
    if (loc.includes('big pine')) return 'Big Pine Key';
    if (loc.includes('little torch')) return 'Little Torch Key';
    if (loc.includes('summerland')) return 'Summerland Key';
    if (loc.includes('duck key')) return 'Duck Key';
    return 'Lower Keys';
}

// Activity detection
function matchesActivity(tour, activity) {
    if (!activity) return true;
    const tags = (tour.tags || []).join(' ').toLowerCase();
    const name = (tour.name || '').toLowerCase();
    const desc = (tour.description || '').toLowerCase();
    
    const activityMap = {
        'snorkel': ['snorkel'],
        'scuba': ['scuba'],
        'wreck': ['wreck', 'shipwreck'],
        'reef': ['reef', 'coral'],
        'boat': ['boat tour', 'cruise', 'charter'],
        'fishing': ['fish', 'angling'],
        'offshore': ['offshore', 'deep sea', 'gulf stream'],
        'backcountry': ['backcountry', 'back country', 'flats'],
        'lobster': ['lobster', 'lobstering'],
        'sunset': ['sunset'],
        'dolphin': ['dolphin'],
        'shark': ['shark'],
        'sandbar': ['sandbar', 'sand bar'],
        'eco': ['eco', 'nature', 'wildlife', 'mangrove'],
        'kayak': ['kayak'],
        'paddleboard': ['paddleboard', 'paddle board', 'sup', 'stand up paddle'],
        'jet-ski': ['jet ski', 'jetski', 'waverunner', 'jet-ski'],
        'sailing': ['sail'],
        'catamaran': ['catamaran'],
        'parasail': ['parasail'],
        'kiteboard': ['kiteboard', 'kite board', 'kitesurf'],
        'tiki': ['tiki', 'bar crawl', 'pub crawl', 'bar hop'],
        'party': ['party', 'booze cruise'],
        'rental': ['rental'],
        'ghost': ['ghost', 'haunted', 'cemetery'],
        'walking': ['walking tour', 'walk tour', 'historic tour'],
        'food': ['food tour', 'culinary', 'tasting', 'dinner', 'brunch'],
        'museum': ['museum', 'aquarium', 'exhibit', 'attraction', 'fort', 'lighthouse'],
        'private': ['private']
    };
    
    const keywords = activityMap[activity] || [activity];
    return keywords.some(kw => tags.includes(kw) || name.includes(kw) || desc.includes(kw));
}

function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// Format price
function formatPrice(price, confidence) {
    if (!Number.isFinite(price) || price <= 0) return 'Price on request';
    if (confidence === 'low') return 'Price on request';
    return `From $${price}`;
}

// Is this row's price good enough to put in front of a visitor?
//
// Measured 2026-08-20 on the rendered DOM: 728 of the 1,279 active rows (56.9%)
// fail this test, so the shuffled 24-card grid was spending an average of 13.83
// of its 24 slots on cards reading "Price on request" (12 homepage loads, min 11,
// max 18) against 2.50 slots in the $40-197 band that has produced every booking
// this network has made.
//
// Deliberately mirrors formatPrice() above — anything that renders as
// "Price on request" must not be drawn — plus a $1 floor. Two rows publish a
// literal $1 placeholder and render "From $1": pk 455365 (Hound Dawg Charters)
// and pk 544282 (Sunset Watersports). Excluded by the rule, not by pk, so a
// third $1 row lands on the same side of it. The rule catches exactly those two
// today; no active row sits at 0 or between 1 and 10.
function hasUsablePrice(tour) {
    if (!Number.isFinite(tour.price) || tour.price <= 1) return false;
    if (tour.priceConfidence === 'low') return false;
    return true;
}

// Clean location display
function cleanLocation(location = '') {
    return location
        .replace(/^United States\/Florida\//, '')
        .replace(/^Florida\//, '')
        .trim() || 'Key West';
}

// Score label
function scoreLabel(score) {
    if (score >= 90) return 'Top Rated';
    if (score >= 75) return 'Popular';
    return '';
}

// Format duration
function formatDuration(minutes) {
    if (!minutes) return '';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours && mins) return `${hours}h ${mins}m`;
    if (hours) return `${hours}h`;
    return `${mins}m`;
}

// Create tour card HTML
function createTourCard(tour) {
    const area = getArea(tour.location);
    const areaName = getAreaName(tour.location);
    const priceDisplay = formatPrice(tour.price, tour.priceConfidence);
    const priceHtml = priceDisplay ? `<div class="tour-price">${priceDisplay}</div>` : '';
    const duration = formatDuration(tour.duration);

    const badges = [];
    const score = tour.qualityScore || 0;
    const badge = scoreLabel(score);
    if (badge) badges.push(`<span class="badge badge-quality">⭐ ${escapeHtml(badge)}</span>`);

    const ratingHtml = tour.rating ?
        `<span class="tour-rating">★ ${escapeHtml(String(tour.rating))}${tour.reviewCount ? ` (${escapeHtml(String(tour.reviewCount))})` : ''}</span>` : '';

    const desc = (tour.description || '').replace(/\s+/g, ' ').trim();

    // Inline-onclick safe escape: JS-escape backslash + apostrophe FIRST, then HTML-escape.
    // Browser HTML-decodes the attribute value before passing to JS; JS-escape sequences (\\, \')
    // survive HTML decoding, so the JS string literal stays well-formed.
    const jsHtmlEscape = (s) => escapeHtml(String(s ?? '').replace(/\\/g, '\\\\').replace(/'/g, "\\'"));
    const onclickName = jsHtmlEscape(tour.name);
    const onclickId = jsHtmlEscape(tour.id);
    const onclickArea = jsHtmlEscape(area);

    const schema = generateTourSchema(tour);
    const schemaJson = JSON.stringify(schema).replace(/<\/script/gi, '<\\/script');

    return `
        <article class="tour-card" data-id="${escapeHtml(tour.id)}">
            <script type="application/ld+json">${schemaJson}</script>
            <div class="tour-image">
                <img src="${tour.image || FALLBACK_IMAGE}" alt="${escapeHtml(tour.name)}" loading="lazy" width="400" height="300" onerror="this.src='${FALLBACK_IMAGE}'" style="width: 100%; height: auto; object-fit: cover;">
                ${priceHtml}
                <div class="tour-badges">${badges.join('')}</div>
                <div class="tour-location">📍 ${escapeHtml(areaName)}</div>
            </div>
            <div class="tour-content">
                <div class="tour-company">${escapeHtml(tour.company)}</div>
                <h3 class="tour-name">${escapeHtml(tour.name)}</h3>
                <div class="tour-meta">
                    ${duration ? `<span>🕐 ${escapeHtml(duration)}</span>` : ''}
                    ${ratingHtml}
                </div>
                ${desc ? `<p class="tour-desc">${escapeHtml(desc)}</p>` : ''}
                <a href="${tour.bookingUrl}"
                   target="_blank"
                   rel="noopener"
                   class="tour-cta"
                   onclick="trackBookingClickEnhanced('${onclickName}', '${onclickId}', '${onclickArea}')">
                    Check Availability →
                </a>
            </div>
        </article>
    `;
}

// GA4 Tracking Functions
function trackBookingClickEnhanced(tourName, tourId, area) {
    gtag('event', 'booking_click', {
        tour_id: tourId,
        tour_name: tourName,
        area: area,
        event_category: 'conversion'
    });
}

function trackFilterChange(filterType, value) {
    gtag('event', 'filter_used', {
        filter_type: filterType,
        value: value,
        event_category: 'engagement'
    });
}

function trackSearchUsed(searchTerm) {
    gtag('event', 'search_used', {
        query: searchTerm,
        event_category: 'engagement'
    });
}

function trackLoadMoreClick() {
    gtag('event', 'load_more_clicked', {
        event_category: 'engagement'
    });
}

// Filter tours
function applyFilters() {
    const areaFilter = document.getElementById('areaFilter')?.value || '';
    const activityFilter = document.getElementById('activityFilter')?.value || '';
    const priceFilter = document.getElementById('priceFilter')?.value || '';
    const sortFilter = document.getElementById('sortFilter')?.value || 'quality';
    const searchQuery = (document.getElementById('hero-search')?.value || '').toLowerCase().trim();
    
    // Track filter usage
    if (areaFilter) trackFilterChange('area', areaFilter);
    if (activityFilter) trackFilterChange('activity', activityFilter);
    if (priceFilter) trackFilterChange('price', priceFilter);
    if (searchQuery) trackSearchUsed(searchQuery);
    
    filteredTours = allTours.filter(tour => {
        // Area filter
        if (areaFilter && getArea(tour.location) !== areaFilter) return false;
        
        // Activity filter
        if (activityFilter && !matchesActivity(tour, activityFilter)) return false;
        
        // Price filter
        if (priceFilter && tour.price) {
            const [min, max] = priceFilter.split('-').map(Number);
            if (tour.price < min || tour.price > max) return false;
        } else if (priceFilter && !tour.price) {
            return false; // Hide tours without price when filtering by price
        }
        
        // Search
        if (searchQuery) {
            const searchable = `${tour.name} ${tour.company} ${tour.description || ''} ${(tour.tags || []).join(' ')}`.toLowerCase();
            if (!searchable.includes(searchQuery)) return false;
        }
        
        return true;
    });
    
    // Sort
    switch (sortFilter) {
        case 'price-low':
            filteredTours.sort((a, b) => (a.price || 9999) - (b.price || 9999));
            break;
        case 'price-high':
            filteredTours.sort((a, b) => (b.price || 0) - (a.price || 0));
            break;
        case 'name':
            filteredTours.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
            break;
        case 'quality':
            filteredTours.sort((a, b) => (b.qualityScore || 0) - (a.qualityScore || 0));
            break;
        case 'shuffle':
        default:
            // Re-shuffle for variety (per page load)
            filteredTours = shuffleArray(filteredTours);
            break;
    }
    
    displayedCount = 0;
    renderTours();
}

// Render tours
function renderTours() {
    const grid = document.getElementById('tours-grid');
    const loadMoreBtn = document.getElementById('load-more');
    const countEl = document.getElementById('tours-count');
    
    if (!grid) return;
    
    const toursToShow = filteredTours.slice(0, displayedCount + TOURS_PER_PAGE);
    displayedCount = toursToShow.length;
    
    if (toursToShow.length === 0) {
        grid.innerHTML = '<p class="loading">No tours found. Try adjusting your filters.</p>';
        if (loadMoreBtn) loadMoreBtn.style.display = 'none';
    } else {
        grid.innerHTML = toursToShow.map(createTourCard).join('');
        if (loadMoreBtn) {
            loadMoreBtn.style.display = displayedCount < filteredTours.length ? 'block' : 'none';
        }
    }
    
    if (countEl) {
        countEl.textContent = `Showing ${displayedCount} of ${filteredTours.length} tours`;
    }
}

// Load more
function loadMore() {
    trackLoadMoreClick();
    const grid = document.getElementById('tours-grid');
    const loadMoreBtn = document.getElementById('load-more');

    // No grid on this page — this function was never meant to run here.
    if (!grid) return;

    const nextTours = filteredTours.slice(displayedCount, displayedCount + TOURS_PER_PAGE);
    displayedCount += nextTours.length;
    
    grid.innerHTML += nextTours.map(createTourCard).join('');
    
    if (loadMoreBtn) {
        loadMoreBtn.style.display = displayedCount < filteredTours.length ? 'block' : 'none';
    }
    
    const countEl = document.getElementById('tours-count');
    if (countEl) {
        countEl.textContent = `Showing ${displayedCount} of ${filteredTours.length} tours`;
    }
}

// Shuffle tours (manual button)
function shuffleTours() {
    filteredTours = shuffleArray(filteredTours);
    displayedCount = 0;
    renderTours();
}

// Clear filters
function clearFilters() {
    const DEFAULTS = { areaFilter: '', activityFilter: '', priceFilter: '', sortFilter: 'quality', 'hero-search': '' };
    const ids = Object.keys(DEFAULTS);
    const els = ids.map(id => document.getElementById(id));

    // No filter controls on this page — this function was never meant to run here.
    if (!els.some(Boolean)) return;

    ids.forEach((id, i) => { if (els[i]) els[i].value = DEFAULTS[id]; });
    applyFilters();
}

// Scroll to tours
function scrollToTours() {
    const searchValue = document.getElementById('hero-search')?.value;
    if (searchValue) {
        applyFilters();
    }
    document.getElementById('tours-section')?.scrollIntoView({ behavior: 'smooth' });
}

// Mobile nav toggle
document.querySelector('.nav-toggle')?.addEventListener('click', () => {
    document.querySelector('.nav-mobile')?.classList.toggle('active');
});

// Initialize
async function init() {
    try {
        const response = await fetch('tours-data.json');
        const _raw = await response.json();
        allTours = Array.isArray(_raw) ? _raw : _raw.tours;
        // Hide tours with a dead FareHarbor booking link (audit 2026-05-28).
        allTours = allTours.filter(t => t.status !== 'inactive' && !t.bookingDead);

        // Only priced inventory is eligible for the draw (see hasUsablePrice).
        allTours = allTours.filter(hasUsablePrice);

        // Count what the grid can actually draw, not the raw active count. This
        // call sat ABOVE the filter and advertised 1,279 while the grid drew from
        // 551. "Verified" cannot mean "we never checked what it costs".
        updateVerifiedToursCount(allTours.length);

        // Shuffle initially for variety (per page load)
        allTours = shuffleArray(allTours);

        filteredTours = [...allTours];
        applyFilters();

        // Event listeners for filters
        ['areaFilter', 'activityFilter', 'priceFilter', 'sortFilter'].forEach(id => {
            document.getElementById(id)?.addEventListener('change', applyFilters);
        });
        
        // Search on enter
        document.getElementById('hero-search')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                applyFilters();
                scrollToTours();
            }
        });
        
    } catch (error) {
        console.error('Error loading tours:', error);
        // Only surface the message where there is somewhere to put it. Without this
        // check the handler itself threw on every page that loads app.js but has no
        // #tours-grid, stacking a second uncaught exception on top of the first.
        const grid = document.getElementById('tours-grid');
        if (grid) grid.innerHTML = '<p class="loading">Error loading tours. Please refresh.</p>';
    }
}

// Area page initialization (for key-west.html, marathon.html, etc.)
async function initAreaPage(areaSlug) {
    try {
        const response = await fetch('tours-data.json');
        const _raw = await response.json();
        allTours = Array.isArray(_raw) ? _raw : _raw.tours;
        allTours = allTours.filter(t => t.status !== 'inactive' && !t.bookingDead);

        // Only priced inventory is eligible for the draw (see hasUsablePrice).
        // islamorada is left with 23 eligible rows against TOURS_PER_PAGE = 24 and
        // renders 23 cards. Accepted: that page was showing an expected 18.1 cards
        // reading "Price on request" out of 24, so it trades one slot for 17.1
        // usable ones. Do not special-case it.
        allTours = allTours.filter(hasUsablePrice);

        // Filter to this area only
        allTours = allTours.filter(tour => getArea(tour.location) === areaSlug);

        // Shuffle (per page load)
        allTours = shuffleArray(allTours);

        filteredTours = [...allTours];
        applyFilters();
        
        // Event listeners
        ['activityFilter', 'priceFilter', 'sortFilter'].forEach(id => {
            document.getElementById(id)?.addEventListener('change', applyFilters);
        });
        
    } catch (error) {
        console.error('Error loading tours:', error);
    }
}

// Start
document.addEventListener('DOMContentLoaded', init);

// ===== TOURISTTIP SCHEMA INJECTION =====
function generateTourSchema(tour) {
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

// ===== STICKY MOBILE CTA BAR =====

// No page that loads app.js has an element with id="tours" — the two pages that
// define one (private-boat-charters, bachelorette-party-boats) do not load this
// file. The bar's own markup varies by page type, so resolve against what is
// actually present: the tours section, then its grid, then a booking anchor.
function resolveBookingTarget() {
    return document.getElementById('tours-section')
        || document.getElementById('tours-grid')
        || document.getElementById('tours')
        || document.querySelector('a[href*="fareharbor.com"]');
}

document.addEventListener('DOMContentLoaded', () => {
    // A bar with nothing to scroll to is a CTA that does nothing; 16 of the 33
    // pages loading this file have no target at all. Ship it only where it works.
    if (!resolveBookingTarget()) return;

    // Create sticky CTA bar
    const stickyBar = document.createElement('div');
    stickyBar.id = 'sticky-cta-bar';
    stickyBar.style.cssText = `
        display: none;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 48px;
        background: #1a472a;
        border-top: 1px solid rgba(26, 71, 42, 0.2);
        /* Below .mobile-cta (100) so it never covers that working control. */
        z-index: 90;
        padding: 0 1rem;
        align-items: center;
        justify-content: center;
        box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.1);
        animation: slideUp 300ms ease-out;
    `;
    
    const button = document.createElement('button');
    button.textContent = 'Book Your Tour';
    button.style.cssText = `
        background: white;
        color: #1a472a;
        padding: 12px 24px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 14px;
        width: 100%;
        max-width: 300px;
        border: none;
        cursor: pointer;
        transition: all 150ms ease;
    `;
    
    button.addEventListener('click', () => {
        // Re-resolve on click: the grid is rendered asynchronously, so the target
        // present at DOMContentLoaded may not be the best one by the time it fires.
        const target = resolveBookingTarget();
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
    
    button.addEventListener('mouseover', () => {
        button.style.transform = 'scale(1.02)';
    });
    
    button.addEventListener('mouseout', () => {
        button.style.transform = 'scale(1)';
    });
    
    stickyBar.appendChild(button);
    document.body.appendChild(stickyBar);
    
    // Add CSS animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideUp {
            from {
                transform: translateY(100%);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        
        @media (max-width: 768px) {
            #sticky-cta-bar {
                display: flex !important;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Show sticky bar after scrolling past hero
    const heroSection = document.querySelector('.hero') || document.querySelector('header');
    let heroScrolled = false;
    
    window.addEventListener('scroll', () => {
        const scrolled = window.scrollY > (heroSection?.offsetHeight || 300);
        
        if (scrolled && !heroScrolled) {
            stickyBar.style.display = 'flex';
            heroScrolled = true;
        } else if (!scrolled && heroScrolled) {
            stickyBar.style.display = 'none';
            heroScrolled = false;
        }
    });
});
