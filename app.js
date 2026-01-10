// Key West Sandbar Tours - App.js
// Tour rendering, filtering, and click tracking

let allTours = [];
let filteredTours = [];
let displayedCount = 0;
const TOURS_PER_PAGE = 24;

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
    
    const activityMap = {
        'snorkel': ['snorkel', 'reef'],
        'boat': ['boat', 'cruise', 'charter'],
        'fishing': ['fish', 'angling'],
        'sunset': ['sunset'],
        'dolphin': ['dolphin'],
        'kayak': ['kayak', 'paddle'],
        'jet-ski': ['jet ski', 'jetski', 'waverunner'],
        'scuba': ['scuba', 'dive', 'diving'],
        'sailing': ['sail', 'catamaran'],
        'parasail': ['parasail'],
        'private': ['private']
    };
    
    const keywords = activityMap[activity] || [activity];
    return keywords.some(kw => tags.includes(kw) || name.includes(kw));
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
    const priceHtml = tour.price ? `<div class="tour-price">From $${tour.price}</div>` : '';
    const duration = formatDuration(tour.duration);
    
    const badges = [];
    if (tour.qualityScore >= 95) badges.push('<span class="badge badge-top">⭐ Top Rated</span>');
    
    const ratingHtml = tour.rating ? 
        `<span class="tour-rating">★ ${tour.rating}${tour.reviewCount ? ` (${tour.reviewCount})` : ''}</span>` : '';
    
    const desc = tour.description ? 
        (tour.description.length > 120 ? tour.description.slice(0, 120) + '...' : tour.description) : '';
    
    const safeName = (tour.name || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
    
    return `
        <article class="tour-card">
            <div class="tour-image">
                <img src="${tour.image}" alt="${tour.name}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400'">
                ${priceHtml}
                <div class="tour-badges">${badges.join('')}</div>
                <div class="tour-location">📍 ${areaName}</div>
            </div>
            <div class="tour-content">
                <div class="tour-company">${tour.company}</div>
                <h3 class="tour-name">${tour.name}</h3>
                <div class="tour-meta">
                    ${duration ? `<span>🕐 ${duration}</span>` : ''}
                    ${ratingHtml}
                </div>
                ${desc ? `<p class="tour-desc">${desc}</p>` : ''}
                <a href="${tour.bookingLink}" 
                   target="_blank" 
                   rel="noopener" 
                   class="tour-cta"
                   onclick="trackBookingClick('${safeName}', '${tour.id}', '${area}')">
                    Check Availability →
                </a>
            </div>
        </article>
    `;
}

// Filter tours
function applyFilters() {
    const areaFilter = document.getElementById('areaFilter')?.value || '';
    const activityFilter = document.getElementById('activityFilter')?.value || '';
    const priceFilter = document.getElementById('priceFilter')?.value || '';
    const sortFilter = document.getElementById('sortFilter')?.value || 'quality';
    const searchQuery = (document.getElementById('hero-search')?.value || '').toLowerCase().trim();
    
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
            // Re-shuffle for variety
            for (let i = filteredTours.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [filteredTours[i], filteredTours[j]] = [filteredTours[j], filteredTours[i]];
            }
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
    const grid = document.getElementById('tours-grid');
    const loadMoreBtn = document.getElementById('load-more');
    
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

// Shuffle tours
function shuffleTours() {
    for (let i = filteredTours.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [filteredTours[i], filteredTours[j]] = [filteredTours[j], filteredTours[i]];
    }
    displayedCount = 0;
    renderTours();
}

// Clear filters
function clearFilters() {
    document.getElementById('areaFilter').value = '';
    document.getElementById('activityFilter').value = '';
    document.getElementById('priceFilter').value = '';
    document.getElementById('sortFilter').value = 'quality';
    document.getElementById('hero-search').value = '';
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
        allTours = await response.json();
        
        // Shuffle initially for variety
        for (let i = allTours.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [allTours[i], allTours[j]] = [allTours[j], allTours[i]];
        }
        
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
        document.getElementById('tours-grid').innerHTML = '<p class="loading">Error loading tours. Please refresh.</p>';
    }
}

// Area page initialization (for key-west.html, marathon.html, etc.)
async function initAreaPage(areaSlug) {
    try {
        const response = await fetch('tours-data.json');
        allTours = await response.json();
        
        // Filter to this area only
        allTours = allTours.filter(tour => getArea(tour.location) === areaSlug);
        
        // Shuffle
        for (let i = allTours.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [allTours[i], allTours[j]] = [allTours[j], allTours[i]];
        }
        
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
