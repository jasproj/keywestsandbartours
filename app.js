/* ============================================
   KEY WEST SANDBAR TOURS - MAIN APPLICATION
   ============================================ */

const CONFIG = {
    toursPerPage: 12,
    fomoInterval: 45000,
    fomoNames: [
        'Sarah from Miami', 'Mike from Tampa', 'Jennifer from Orlando',
        'David from Atlanta', 'Lisa from Chicago', 'Chris from New York',
        'Amanda from Boston', 'Brian from Dallas', 'Emily from Denver',
        'Kevin from Nashville', 'Rachel from Charlotte', 'Jason from Phoenix',
        'Michelle from Philadelphia', 'Ryan from Seattle', 'Stephanie from Austin',
        'Tom from San Diego', 'Katie from Portland', 'Dan from Detroit'
    ],
    fomoActions: [
        'just booked a sandbar tour!',
        'just booked a sunset cruise!',
        'just booked a snorkel trip!',
        'just booked a dolphin tour!',
        'just booked a jet ski rental!',
        'just booked a fishing charter!',
        'just booked a parasailing trip!',
        'just booked a boat tour!'
    ]
};

// State
let allTours = [];
let filteredTours = [];
let displayedCount = 0;
let currentFilters = {
    island: '',
    activity: '',
    search: '',
    sort: 'random'
};

// COMPREHENSIVE Search synonyms - maps user input to tour tags/content
const SYNONYMS = {
    // Key West Specific
    'sandbar': ['Sandbar', 'sand bar', 'sandbars', 'backcountry', 'flats', 'shallow'],
    'backcountry': ['backcountry', 'backwater', 'flats', 'mangrove', 'sandbar'],
    'duval': ['duval', 'downtown', 'old town', 'city', 'walking'],
    'mallory': ['mallory', 'sunset', 'celebration', 'square'],
    
    // Water Activities
    'snorkel': ['Snorkel', 'snorkeling', 'reef', 'underwater', 'coral'],
    'scuba': ['Scuba', 'diving', 'dive', 'underwater', 'tank', 'certification'],
    'swim': ['swim', 'swimming', 'snorkel', 'water'],
    
    // Marine Life
    'dolphin': ['Dolphin', 'dolphins', 'swim with dolphins', 'pod', 'bottlenose'],
    'turtle': ['turtle', 'sea turtle', 'green sea', 'loggerhead'],
    'shark': ['shark', 'shark dive', 'cage', 'nurse shark'],
    'fish': ['Fishing', 'fish', 'deep sea', 'sportfishing', 'charter', 'reef fish'],
    'manatee': ['manatee', 'sea cow', 'wildlife'],
    'stingray': ['stingray', 'ray', 'rays'],
    
    // Boat Types
    'boat': ['Boat Tour', 'Boat Rental', 'cruise', 'vessel', 'charter'],
    'sail': ['Sailing', 'Catamaran', 'sail', 'sailboat', 'yacht', 'schooner'],
    'catamaran': ['Catamaran', 'cat', 'sailing'],
    'kayak': ['Kayak', 'kayaking', 'paddle', 'paddling'],
    'paddleboard': ['SUP', 'stand up paddle', 'paddleboard', 'paddle board'],
    'jet': ['Jet Ski', 'jetski', 'waverunner', 'watercraft', 'jet ski'],
    'pontoon': ['pontoon', 'party boat', 'deck boat'],
    
    // Air Activities
    'parasail': ['Parasail', 'parasailing', 'parachute', 'sky'],
    'seaplane': ['seaplane', 'plane', 'flight', 'aerial'],
    'helicopter': ['helicopter', 'heli', 'aerial', 'flight'],
    
    // Fishing Types
    'fishing': ['Fishing', 'fish', 'charter', 'angling'],
    'offshore': ['offshore', 'deep sea', 'gulf stream', 'sportfish'],
    'reef fishing': ['reef', 'bottom fishing', 'snappers', 'grouper'],
    'flats': ['flats', 'backcountry', 'tarpon', 'bonefish', 'permit'],
    'lobster': ['lobster', 'lobstering', 'mini season', 'bug'],
    
    // Tours & Experiences
    'food': ['Food Tour', 'food', 'culinary', 'tasting', 'dining', 'restaurant', 'crawl'],
    'history': ['History Tour', 'historical', 'ghost', 'haunted', 'heritage', 'hemingway'],
    'ghost': ['ghost', 'haunted', 'paranormal', 'spooky', 'night'],
    'eco': ['Eco Tour', 'eco', 'nature', 'wildlife', 'environmental', 'mangrove'],
    'wildlife': ['Wildlife', 'nature', 'animals', 'birds', 'sanctuary'],
    'bar': ['bar', 'pub', 'crawl', 'drinks', 'drinking', 'party'],
    
    // Time of Day
    'sunset': ['Sunset', 'sunset cruise', 'evening', 'dusk', 'golden hour'],
    'sunrise': ['sunrise', 'morning', 'dawn', 'early'],
    'night': ['night', 'evening', 'stargazing', 'after dark', 'nocturnal'],
    
    // Experience Types
    'private': ['Private', 'exclusive', 'charter', 'vip', 'custom', 'personalized'],
    'family': ['family', 'kids', 'children', 'kid friendly', 'all ages'],
    'romantic': ['romantic', 'couples', 'honeymoon', 'anniversary', 'proposal'],
    'party': ['party', 'celebration', 'bachelor', 'bachelorette', 'group'],
    'adventure': ['adventure', 'extreme', 'thrill', 'adrenaline', 'exciting'],
    'relaxing': ['relaxing', 'peaceful', 'calm', 'serene', 'gentle'],
    'luxury': ['luxury', 'premium', 'upscale', 'high end', 'deluxe'],
    
    // Key West Landmarks
    'southernmost': ['southernmost', 'point', 'landmark', 'photo'],
    'dry tortugas': ['dry tortugas', 'tortugas', 'fort jefferson', 'national park'],
    'fort': ['fort', 'fort jefferson', 'fort zachary', 'military'],
    'hemingway': ['hemingway', 'author', 'cats', 'museum', 'house'],
    'reef': ['reef', 'coral', 'barrier reef', 'snorkel', 'dive']
};

// Location keywords for smarter matching
const LOCATION_KEYWORDS = {
    'key west': ['key west', 'old town', 'duval', 'mallory', 'southernmost', 'downtown'],
    'stock island': ['stock island', 'safe harbor', 'working waterfront', 'six fins'],
    'lower keys': ['lower keys', 'sugarloaf', 'summerland', 'big pine', 'cudjoe']
};

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    setupEventListeners();
    await loadTours();
    initMobileMenu();
    initStickyHeader();
    initMobileCTA();
    initFOMO();
    initWeather();
    initializeFAQs();
    checkURLParams();
}

// ============================================
// DATA LOADING
// ============================================

async function loadTours() {
    try {
        // Cache-bust to ensure fresh data
        const response = await fetch('tours-data.json?t=' + Date.now());
        allTours = await response.json();
        
        // Get recently shown tours from localStorage
        const recentlyShown = JSON.parse(localStorage.getItem('kwst_recent') || '[]');
        
        // Crypto-grade shuffle
        allTours = cryptoShuffle([...allTours]);
        
        // Move recently shown tours to the back so they don't appear first
        if (recentlyShown.length > 0) {
            const notRecent = allTours.filter(t => !recentlyShown.includes(t.id));
            const recent = allTours.filter(t => recentlyShown.includes(t.id));
            allTours = [...cryptoShuffle(notRecent), ...cryptoShuffle(recent)];
        }
        
        // Store first 48 tour IDs as "recently shown" (4 pages worth)
        const newRecent = allTours.slice(0, 48).map(t => t.id);
        localStorage.setItem('kwst_recent', JSON.stringify(newRecent));
        
        // Update tour count in trust bar
        const tourCountEl = document.getElementById('tour-count');
        if (tourCountEl) {
            tourCountEl.textContent = allTours.length;
        }
        
        applyFilters();
    } catch (error) {
        console.error('Error loading tours:', error);
        document.getElementById('tours-grid').innerHTML = `
            <div class="loading-state">
                <p>Unable to load tours. Please refresh the page.</p>
            </div>
        `;
    }
}

// Crypto-grade shuffle using crypto.getRandomValues
function cryptoShuffle(array) {
    const n = array.length;
    if (n === 0) return array;
    
    // Use crypto API for true randomness
    if (window.crypto && window.crypto.getRandomValues) {
        const randomValues = new Uint32Array(n);
        window.crypto.getRandomValues(randomValues);
        
        for (let i = n - 1; i > 0; i--) {
            const j = randomValues[i] % (i + 1);
            [array[i], array[j]] = [array[j], array[i]];
        }
    } else {
        // Fallback
        for (let i = n - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
    }
    return array;
}

// ============================================
// FILTERING & SEARCH
// ============================================

function applyFilters() {
    filteredTours = allTours.filter(tour => {
        // Island/Area filter
        if (currentFilters.island && tour.island.toLowerCase() !== currentFilters.island.toLowerCase()) {
            return false;
        }
        
        // Activity filter
        if (currentFilters.activity && !tour.tags.some(tag => 
            tag.toLowerCase().includes(currentFilters.activity.toLowerCase())
        )) {
            return false;
        }
        
        // Search filter with synonyms
        if (currentFilters.search) {
            const searchTerms = currentFilters.search.toLowerCase().split(' ').filter(t => t.length > 0);
            const searchableContent = `${tour.name} ${tour.company} ${tour.tags.join(' ')} ${tour.location}`.toLowerCase();
            
            const matchesSearch = searchTerms.some(term => {
                // Direct match
                if (searchableContent.includes(term)) return true;
                
                // Synonym match
                for (const [key, synonyms] of Object.entries(SYNONYMS)) {
                    if (key.includes(term) || synonyms.some(s => s.toLowerCase().includes(term))) {
                        if (searchableContent.includes(key) || synonyms.some(s => searchableContent.includes(s.toLowerCase()))) {
                            return true;
                        }
                    }
                }
                
                // Location keyword match
                for (const [location, keywords] of Object.entries(LOCATION_KEYWORDS)) {
                    if (keywords.some(k => k.includes(term))) {
                        if (tour.island.toLowerCase() === location) {
                            return true;
                        }
                    }
                }
                
                // Fuzzy match (60% threshold)
                const words = searchableContent.split(/\s+/);
                return words.some(word => {
                    if (word.length < 3 || term.length < 3) return false;
                    const matches = [...term].filter((char, i) => word[i] === char).length;
                    return matches / Math.max(term.length, word.length) >= 0.6;
                });
            });
            
            if (!matchesSearch) return false;
        }
        
        return true;
    });
    
    // Sort (random shuffles every time for true randomization)
    if (currentFilters.sort === 'quality') {
        filteredTours.sort((a, b) => (b.qualityScore || 0) - (a.qualityScore || 0));
    } else if (currentFilters.sort === 'name') {
        filteredTours.sort((a, b) => a.name.localeCompare(b.name));
    } else {
        // 'random' - shuffle filtered results fresh every time
        filteredTours = cryptoShuffle([...filteredTours]);
    }
    
    // Reset display
    displayedCount = 0;
    renderTours(true);
    updateResultsCount();
}

function renderTours(reset = false) {
    const grid = document.getElementById('tours-grid');
    const loadMoreBtn = document.getElementById('load-more');
    
    if (reset) {
        grid.innerHTML = '';
        displayedCount = 0;
    }
    
    const toShow = filteredTours.slice(displayedCount, displayedCount + CONFIG.toursPerPage);
    
    if (toShow.length === 0 && displayedCount === 0) {
        grid.innerHTML = `
            <div class="loading-state">
                <p>No tours found matching your criteria. Try adjusting your filters.</p>
            </div>
        `;
        loadMoreBtn.classList.add('hidden');
        return;
    }
    
    toShow.forEach((tour, idx) => {
        const card = createTourCard(tour, displayedCount + idx);
        grid.appendChild(card);
    });
    
    displayedCount += toShow.length;
    
    // Show/hide load more button
    if (displayedCount >= filteredTours.length) {
        loadMoreBtn.classList.add('hidden');
    } else {
        loadMoreBtn.classList.remove('hidden');
    }
}

function createTourCard(tour, index) {
    const card = document.createElement('div');
    card.className = 'tour-card';
    
    const tagsHTML = tour.tags.slice(0, 3).map(tag => 
        `<span class="tour-tag">${tag}</span>`
    ).join('');
    
    // Add Popular badge only for genuinely high-rated tours (not position-based)
    const isPopular = tour.qualityScore >= 95;
    const popularBadge = isPopular ? '<span class="popular-badge">Popular</span>' : '';
    
    // Price ribbon
    const priceRibbon = tour.price ? `<span class="price-ribbon">${tour.price}</span>` : '';
    
    // Description (truncate to ~100 chars for card display)
    let descHTML = '';
    if (tour.description) {
        const shortDesc = tour.description.length > 120 
            ? tour.description.substring(0, 117) + '...' 
            : tour.description;
        descHTML = `<p class="tour-description">${shortDesc}</p>`;
    }
    
    card.innerHTML = `
        <div class="tour-card-img">
            ${popularBadge}
            ${priceRibbon}
            <img src="${tour.image}" alt="${tour.name}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=400'">
            <span class="tour-location-badge">${tour.location}</span>
        </div>
        <div class="tour-card-content">
            <p class="tour-company">${tour.company}</p>
            <h3 class="tour-name">${tour.name}</h3>
            ${descHTML}
            <div class="tour-tags">${tagsHTML}</div>
            <a href="${tour.bookingLink}" target="_blank" rel="noopener" class="tour-cta">Book Now →</a>
        </div>
    `;
    
    return card;
}

function updateResultsCount() {
    const countEl = document.getElementById('results-count');
    if (filteredTours.length === 0) {
        countEl.textContent = 'No tours found';
    } else if (filteredTours.length === 1) {
        countEl.textContent = '1 adventure found';
    } else {
        countEl.textContent = `${filteredTours.length} adventures found`;
    }
}

// ============================================
// EVENT HANDLERS
// ============================================

function setupEventListeners() {
    // Filter dropdowns
    const islandFilter = document.getElementById('island-filter');
    const activityFilter = document.getElementById('activity-filter');
    const sortFilter = document.getElementById('sort-filter');
    const searchInput = document.getElementById('search-input');
    const heroSearch = document.getElementById('hero-search');
    
    if (islandFilter) {
        islandFilter.addEventListener('change', (e) => {
            currentFilters.island = e.target.value;
            applyFilters();
        });
    }
    
    if (activityFilter) {
        activityFilter.addEventListener('change', (e) => {
            currentFilters.activity = e.target.value;
            applyFilters();
        });
    }
    
    if (sortFilter) {
        sortFilter.addEventListener('change', (e) => {
            currentFilters.sort = e.target.value;
            applyFilters();
        });
    }
    
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                currentFilters.search = e.target.value;
                applyFilters();
            }, 300);
        });
    }
    
    // Hero search
    if (heroSearch) {
        heroSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                executeHeroSearch();
            }
        });
    }
    
    // Email form
    const emailForm = document.getElementById('email-form');
    if (emailForm) {
        emailForm.addEventListener('submit', (e) => {
            e.preventDefault();
            alert('Thanks for subscribing! Check your email for the guide.');
            emailForm.reset();
        });
    }
}

function executeHeroSearch() {
    const heroSearch = document.getElementById('hero-search');
    const searchInput = document.getElementById('search-input');
    
    if (heroSearch && heroSearch.value) {
        currentFilters.search = heroSearch.value;
        if (searchInput) {
            searchInput.value = heroSearch.value;
        }
        applyFilters();
        
        // Scroll to tours section
        document.getElementById('tours-section').scrollIntoView({ behavior: 'smooth' });
    }
}

function quickFilter(term) {
    const searchInput = document.getElementById('search-input');
    const heroSearch = document.getElementById('hero-search');
    
    currentFilters.search = term;
    if (searchInput) searchInput.value = term;
    if (heroSearch) heroSearch.value = term;
    
    applyFilters();
    document.getElementById('tours-section').scrollIntoView({ behavior: 'smooth' });
}

function clearAllFilters() {
    currentFilters = { island: '', activity: '', search: '', sort: 'random' };
    
    document.getElementById('island-filter').value = '';
    document.getElementById('activity-filter').value = '';
    document.getElementById('sort-filter').value = 'random';
    document.getElementById('search-input').value = '';
    
    const heroSearch = document.getElementById('hero-search');
    if (heroSearch) heroSearch.value = '';
    
    applyFilters();
}

function loadMoreTours() {
    renderTours(false);
}

function shuffleTours() {
    filteredTours = cryptoShuffle([...filteredTours]);
    displayedCount = 0;
    renderTours(true);
}

// ============================================
// UI COMPONENTS
// ============================================

function initMobileMenu() {
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const mobileNav = document.querySelector('.nav-mobile');
    
    if (menuBtn && mobileNav) {
        menuBtn.addEventListener('click', () => {
            mobileNav.classList.toggle('active');
            menuBtn.classList.toggle('active');
        });
        
        // Close menu when clicking a link
        mobileNav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                mobileNav.classList.remove('active');
                menuBtn.classList.remove('active');
            });
        });
    }
}

function initStickyHeader() {
    const header = document.querySelector('.header');
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
        
        lastScroll = currentScroll;
    });
}

function initMobileCTA() {
    const mobileCTA = document.getElementById('mobile-cta');
    const hero = document.querySelector('.hero');
    
    if (mobileCTA && hero) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    mobileCTA.style.display = 'none';
                } else {
                    mobileCTA.style.display = 'block';
                }
            });
        }, { threshold: 0.1 });
        
        observer.observe(hero);
    }
}

// ============================================
// FOMO NOTIFICATIONS
// ============================================

function initFOMO() {
    // Initial delay before first notification
    setTimeout(() => {
        showFOMONotification();
        setInterval(showFOMONotification, CONFIG.fomoInterval);
    }, 10000);
}

function showFOMONotification() {
    const notification = document.getElementById('notification');
    const nameEl = document.getElementById('notification-name');
    const actionEl = document.getElementById('notification-action');
    
    if (notification && nameEl && actionEl) {
        nameEl.textContent = CONFIG.fomoNames[Math.floor(Math.random() * CONFIG.fomoNames.length)];
        actionEl.textContent = CONFIG.fomoActions[Math.floor(Math.random() * CONFIG.fomoActions.length)];
        
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 5000);
    }
}

// ============================================
// WEATHER WIDGET
// ============================================

async function initWeather() {
    const weatherEl = document.getElementById('header-weather');
    if (!weatherEl) return;
    
    try {
        // Using Open-Meteo (free, no API key needed) for Key West coordinates
        const response = await fetch(
            'https://api.open-meteo.com/v1/forecast?latitude=24.5551&longitude=-81.7800&current_weather=true&temperature_unit=fahrenheit'
        );
        const data = await response.json();
        
        if (data.current_weather) {
            const temp = Math.round(data.current_weather.temperature);
            const weatherCode = data.current_weather.weathercode;
            
            const tempEl = weatherEl.querySelector('.weather-temp');
            const iconEl = weatherEl.querySelector('.weather-icon');
            
            if (tempEl) tempEl.textContent = `${temp}°F`;
            if (iconEl) iconEl.textContent = getWeatherEmoji(weatherCode);
        }
    } catch (error) {
        console.log('Weather fetch failed, using default');
    }
}

function getWeatherEmoji(code) {
    if (code === 0) return '☀️';
    if (code === 1 || code === 2) return '🌤️';
    if (code === 3) return '☁️';
    if (code >= 51 && code <= 67) return '🌧️';
    if (code >= 71 && code <= 77) return '🌨️';
    if (code >= 80 && code <= 82) return '🌦️';
    if (code >= 95) return '⛈️';
    return '☀️';
}

// ============================================
// URL PARAMETERS
// ============================================

function checkURLParams() {
    const params = new URLSearchParams(window.location.search);
    
    const search = params.get('search') || params.get('q');
    const island = params.get('island') || params.get('area');
    const activity = params.get('activity');
    
    if (search) {
        currentFilters.search = search;
        const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.value = search;
    }
    
    if (island) {
        currentFilters.island = island;
        const islandFilter = document.getElementById('island-filter');
        if (islandFilter) islandFilter.value = island;
    }
    
    if (activity) {
        currentFilters.activity = activity;
        const activityFilter = document.getElementById('activity-filter');
        if (activityFilter) activityFilter.value = activity;
    }
    
    if (search || island || activity) {
        applyFilters();
        setTimeout(() => {
            document.getElementById('tours-section')?.scrollIntoView({ behavior: 'smooth' });
        }, 500);
    }
}

// Make functions globally available
window.executeHeroSearch = executeHeroSearch;
window.quickFilter = quickFilter;
window.clearAllFilters = clearAllFilters;
window.loadMoreTours = loadMoreTours;
window.shuffleTours = shuffleTours;

// ============================================
// EMAIL CAPTURE HANDLER
// ============================================

function handleEmailSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const emailInput = form.querySelector('input[type="email"]');
    const email = emailInput.value;
    
    // Store in localStorage for now (would connect to email service)
    const subscribers = JSON.parse(localStorage.getItem('kwst_subscribers') || '[]');
    if (!subscribers.includes(email)) {
        subscribers.push(email);
        localStorage.setItem('kwst_subscribers', JSON.stringify(subscribers));
    }
    
    // Show success message
    const content = form.closest('.email-capture-content');
    content.innerHTML = `
        <h2>🎉 You're In!</h2>
        <p>We'll send you the best last-minute deals and insider tips.</p>
        <p style="font-size: 0.9rem; opacity: 0.8; margin-top: 1rem;">Welcome to the crew!</p>
    `;
}

window.handleEmailSubmit = handleEmailSubmit;

/* ============================================
   RANDOMIZING FAQ SYSTEM
   ============================================ */

const ALL_FAQS = [
    {
        question: "What are the best things to do in Key West?",
        answer: "Top activities include sandbar trips with crystal-clear waters, snorkeling at the only living coral reef in North America, sunset cruises at Mallory Square, dolphin watching, parasailing, fishing charters, jet ski tours, kayaking through mangroves, and exploring Duval Street. We feature the best local tours across all categories."
    },
    {
        question: "What is a sandbar tour?",
        answer: "Sandbar tours take you to shallow sandbars in the backcountry where you can wade in crystal-clear, waist-deep water, relax, swim, and enjoy the stunning Keys scenery. Popular spots include Snipes Point, Woman Key, and Boca Grande. Many tours include snorkeling stops, drinks, and snacks. It's one of the most popular Key West experiences!"
    },
    {
        question: "How do I book tours through Sandbar Tours?",
        answer: "Browse tours, filter by area or activity, and click \"Book Now.\" You'll be connected directly with the tour operator's booking system. Most offer free cancellation 24-48 hours before your activity. We feature over 476 tours from verified local operators."
    },
    {
        question: "What's the best time to visit Key West?",
        answer: "Key West is beautiful year-round! <strong>Winter (Dec–Mar)</strong> has perfect weather and is peak season. <strong>Spring (Apr–May)</strong> offers fewer crowds and great conditions. <strong>Summer & Fall</strong> are warmer with occasional afternoon showers and the best deals on tours and accommodations."
    },
    {
        question: "What should I bring on a boat tour?",
        answer: "Essentials include: reef-safe sunscreen, sunglasses, hat, swimsuit, towel, and water. Most boats provide snorkel gear. Consider bringing a waterproof phone case and motion sickness prevention if you're prone to seasickness. Some tours allow you to bring your own food and drinks (BYOB)."
    },
    {
        question: "Are your prices better than Viator or Expedia?",
        answer: "We connect you directly with local tour operators through their booking systems, so you get their direct prices—no middleman markups. More of your money stays in the Florida Keys' local economy and goes directly to the captains and crew who create your experience."
    },
    {
        question: "Where are the best sandbars in Key West?",
        answer: "The most popular sandbars include Snipes Point (great for beginners), Woman Key (beautiful and secluded), Boca Grande (crystal-clear water), Jewfish Basin (calm and shallow), and the Mud Keys area. Each has its own character, and most sandbar tours visit multiple spots."
    },
    {
        question: "Can I see dolphins in Key West?",
        answer: "Absolutely! Bottlenose dolphins are commonly spotted in the backcountry waters. Dedicated dolphin tours take you to their favorite spots, but you might also see them on sandbar trips, sunset cruises, or even kayak tours. Morning trips often have the best dolphin sightings."
    },
    {
        question: "What is the Florida Keys National Marine Sanctuary?",
        answer: "The sanctuary protects 2,900 square nautical miles of waters surrounding the Keys, including the only living coral barrier reef in the continental United States. All tours operate within these protected waters. Responsible operators help preserve this unique ecosystem for future generations."
    },
    {
        question: "How much do Key West tours typically cost?",
        answer: "Prices vary by activity. Snorkeling trips start around $50-80 per person. Sandbar tours range from $75-150. Private charters run $400-800 for 4 hours. Sunset cruises start at $50. Parasailing is around $80-100. Fishing charters range from $600-1200 depending on duration and boat size."
    },
    {
        question: "Are tours suitable for children?",
        answer: "Most tours welcome children! Sandbar trips are perfect for families—kids love playing in the shallow, calm water. Many operators offer life jackets for little ones. Check individual tour descriptions for age recommendations. Some fishing and diving tours may have minimum age requirements."
    },
    {
        question: "What's the difference between Key West and Stock Island tours?",
        answer: "Key West tours typically depart from marinas near downtown and Old Town. Stock Island (just north of Key West) offers a more local, less touristy experience with excellent fishing and diving operations. Both areas access the same beautiful waters—it's mainly about departure location."
    },
    {
        question: "Do I need to know how to swim for boat tours?",
        answer: "Not necessarily! Many tours offer flotation devices and you can enjoy sandbars while wading in shallow water. However, snorkeling and diving activities do require basic swimming ability. Always let your captain know about your comfort level in the water."
    },
    {
        question: "What is backcountry Key West?",
        answer: "The backcountry refers to the shallow flats, mangrove islands, and sandbars on the Gulf side of Key West (north/northwest). It's calmer than the Atlantic side, with crystal-clear water perfect for sandbar trips, kayaking, paddleboarding, and wildlife watching."
    },
    {
        question: "Can I bring alcohol on boat tours?",
        answer: "Many tours are BYOB (bring your own beverages), while others include drinks or offer a cash bar. Check individual tour descriptions. Some sunset cruises and party boats feature open bars with beer, wine, and cocktails included in the price."
    },
    {
        question: "What if my tour gets cancelled due to weather?",
        answer: "Safety comes first! If weather conditions are unsafe, operators will reschedule or offer a full refund. Most cancellation policies allow free rebooking 24-48 hours in advance. Check individual tour policies, and consider booking early in your trip so you have backup days."
    },
    {
        question: "What is reef-safe sunscreen?",
        answer: "Reef-safe sunscreen is free from oxybenzone and octinoxate—chemicals that damage coral reefs. These ingredients are banned in the Florida Keys. Look for mineral-based sunscreens with zinc oxide or titanium dioxide. Protecting the reef helps preserve Key West's incredible snorkeling."
    },
    {
        question: "How long are most boat tours?",
        answer: "Tour lengths vary: quick trips like parasailing are about 1 hour. Snorkeling and sandbar tours typically run 3-4 hours. Half-day fishing charters are 4-5 hours. Full-day adventures can be 6-8 hours. Sunset cruises are usually 2 hours. Private charters let you customize duration."
    },
    {
        question: "What marine life might I see?",
        answer: "The Keys are home to incredible biodiversity! Expect to see tropical fish (parrotfish, angelfish, tangs), sea turtles, dolphins, manatees (especially in winter), stingrays, nurse sharks, lobsters, starfish, and countless coral species. Lucky visitors spot eagle rays, barracuda, and even whale sharks!"
    },
    {
        question: "Do I need to tip boat captains and crew?",
        answer: "Tipping is customary and appreciated. Standard gratuity is 15-20% of the tour cost, similar to restaurant service. For exceptional service or private charters, 20%+ is common. Tips are often the primary income for crew members. Cash is preferred but some operators accept card tips."
    },
    {
        question: "What's the best snorkeling in Key West?",
        answer: "Top snorkel spots include Sand Key (shallow reef, great for beginners), Eastern Dry Rocks (diverse coral and fish), Western Dry Rocks (larger marine life), and the Vandenberg wreck (advanced). The reef is about 5 miles offshore—you'll need a boat tour to reach it."
    },
    {
        question: "Can I book a private charter?",
        answer: "Yes! Private charters give you exclusive use of a boat with your own captain. Perfect for families, groups, special occasions, or anyone wanting a personalized experience. You can customize the itinerary—combine snorkeling, sandbar time, sunset viewing, or fishing in one trip."
    },
    {
        question: "What happens if I get seasick?",
        answer: "The backcountry (where sandbar tours go) has calmer water than the open ocean. If prone to seasickness, take preventative medication before boarding, stay on deck with fresh air, watch the horizon, and avoid heavy meals. Ginger and acupressure bands can help too."
    },
    {
        question: "Are eco-tours worth it?",
        answer: "Absolutely! Eco-tours offer educational experiences led by knowledgeable guides who share insights about marine ecosystems, wildlife behavior, and conservation. You'll often see more wildlife with guides who know where to look. Plus, eco-operators prioritize sustainable practices."
    },
    {
        question: "What fish can I catch in Key West?",
        answer: "The Keys offer world-class fishing! Inshore: bonefish, permit, tarpon, snook, redfish. Offshore: mahi-mahi, tuna, wahoo, sailfish, marlin. Reef: snapper, grouper, hogfish. Species vary by season. Tarpon fishing (April-July) is legendary. Charter captains know the best spots."
    },
    {
        question: "How far in advance should I book?",
        answer: "During peak season (December-April), book 1-2 weeks ahead for popular tours. Sunset cruises and private charters fill fastest. Off-season, a few days notice is usually fine. Last-minute availability exists, but you'll have fewer choices. Sign up for our deals to catch cancellations!"
    }
];

function initializeFAQs() {
    const container = document.getElementById('faq-container');
    if (!container) return;
    
    // Crypto-grade shuffle for true randomness
    const shuffled = [...ALL_FAQS];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const randomArray = new Uint32Array(1);
        window.crypto.getRandomValues(randomArray);
        const j = randomArray[0] % (i + 1);
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    
    // Display 6 random FAQs
    const selectedFAQs = shuffled.slice(0, 6);
    
    container.innerHTML = selectedFAQs.map(faq => `
        <details class="faq-item">
            <summary>${faq.question}</summary>
            <div class="faq-answer">
                <p>${faq.answer}</p>
            </div>
        </details>
    `).join('');
}

// initializeFAQs is called from initApp()
