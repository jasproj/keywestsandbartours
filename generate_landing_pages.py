#!/usr/bin/env python3
import json
import os

# Load tours data
with open('tours-data.json', 'r') as f:
    all_tours = json.load(f)

# Define pages configuration
pages = [
    {
        'filename': 'sunset-cruises.html',
        'title': 'Key West Sunset Cruises',
        'slug': 'sunset-cruises',
        'meta_desc': 'Private sunset cruises in Key West from $80. Romantic sails, proposals, dinner cruises. Perfect for couples.',
        'h1': 'Key West Sunset Cruises',
        'badge': 'Sunset Sails',
        'intro': """Experience Key West's most iconic moment—the legendary sunset—aboard a private sailing vessel. Our sunset cruises are perfect for romantic evenings, proposals, or simply watching nature's daily masterpiece from the water.

From intimate two-hour sails to full-evening experiences with dinner service, each cruise is tailored to your group. Many operators offer special packages for proposals, anniversaries, and celebrations. You'll sail past Mallory Square and experience where the Gulf of Mexico meets the Atlantic Ocean.

Most sunset cruises operate May through October, departing 5-7 PM depending on seasonal sunsets. Popular options include private sailing charters, catamaran experiences, and glass-bottom boats. Book in advance—during peak season, sunset cruises often sell out 1-2 days ahead.""",
        'faq': [
            {
                'q': 'What time do sunset cruises depart?',
                'a': 'Departure times vary by season. Most cruises depart 5-7 PM, timed to catch the sunset. Your captain will confirm the exact time based on that day\'s sunset time.'
            },
            {
                'q': 'Can you help with a proposal?',
                'a': 'Many operators specialize in proposal packages. Let them know in advance—they can help with timing, champagne, rings, and even photography coordination.'
            },
            {
                'q': 'What if weather is bad?',
                'a': 'Most operators offer full refunds or rescheduling if weather is severe. Cloudy sunsets are often the most dramatic.'
            },
            {
                'q': 'Private vs. shared cruises?',
                'a': 'Private means your group and captain only. Shared cruises have other guests but cost less. Both see the same unforgettable sunset.'
            }
        ],
        'filter_func': lambda t: any(tag in ['Sailing', 'Boat Tour-Sailing', 'Boat Tour'] for tag in t.get('tags', [])) and t.get('timeOfDay') == 'evening'
    },
    {
        'filename': 'snorkeling.html',
        'title': 'Key West Snorkeling Tours',
        'slug': 'snorkeling',
        'meta_desc': 'Best snorkeling tours in Key West. Coral reefs, marine life, shallow waters. Book private or group snorkel tours.',
        'h1': 'Key West Snorkeling Tours',
        'badge': 'Snorkel Adventures',
        'intro': """Discover the underwater treasures of Key West with professional snorkeling tours. From shallow coral gardens teeming with tropical fish to deeper reef systems, our snorkeling experiences offer something for everyone—whether you're a first-timer or experienced snorkeler.

Most tours visit the shallow backcountry reefs or offshore coral formations. You'll encounter colorful tropical fish, sea turtles, rays, and if you're lucky, dolphins. Tours include all gear (mask, fins, snorkel), though many people prefer bringing their own. Water temperatures range from 73°F in winter to 86°F in summer.

Tours typically last 2-4 hours, with 1-2 hours of actual snorkeling time. Most are suitable for families and beginners. Some advanced tours visit deeper reefs with more diverse marine life. Many tours combine snorkeling with other activities like sunset viewing, dolphin watching, or fishing.""",
        'faq': [
            {
                'q': 'Do I need to be a strong swimmer?',
                'a': 'No. Most Key West snorkeling is in shallow, calm water. Guides help beginners feel comfortable. Life jackets available upon request.'
            },
            {
                'q': 'What will I see?',
                'a': 'Tropical fish, sea turtles, rays, starfish, and colorful coral. Occasionally dolphins and nurse sharks (harmless). Marine life varies by location and season.'
            },
            {
                'q': 'Can I bring my own gear?',
                'a': 'Yes, most operators welcome personal gear. All-inclusive tours provide mask, fins, and snorkel. Wetsuits available for cold months.'
            },
            {
                'q': 'How long is the snorkeling time?',
                'a': 'Typical tours are 3-4 hours with 1-2 hours in the water. Some tours offer multiple snorkel sites with time to rest between.'
            }
        ],
        'filter_func': lambda t: any('Snorkel' in tag for tag in t.get('tags', []))
    },
    {
        'filename': 'sandbar-tours.html',
        'title': 'Key West Sandbar Tours',
        'slug': 'sandbar-tours',
        'meta_desc': 'Explore Key West sandbars by boat. Crystal clear shallow waters, perfect for swimming, sunbathing, and photos.',
        'h1': 'Key West Sandbar Tours',
        'badge': 'Sandbar Adventures',
        'intro': """Key West's sandbars are natural wonders—shallow, crystal-clear waters where you can wade and swim in perfect turquoise shallows. These unique formations appear and disappear with tides, creating an ever-changing landscape that's perfect for families, groups, and anyone seeking a quintessential Keys experience.

Sandbar tours combine boat travel, swimming, and social time. Most tours visit multiple shallow-water spots, giving you time to wade, explore, and enjoy the stunning scenery. Many operators provide floating islands (large lilypads or platforms) for lounging, and some include snorkeling opportunities at nearby reefs.

Tours range from 2-6 hours and depart from Key West, Stock Island, or other Keys locations. Most are suitable for all ages and swimming abilities. The best season is late spring through early fall, though tours run year-round. Book in advance during peak season.""",
        'faq': [
            {
                'q': 'What are the sandbars like?',
                'a': 'Shallow (1-4 feet), clear turquoise water. You can wade, swim, and float. Perfect for photos. Exact location varies by tide and season.'
            },
            {
                'q': 'Are they crowded?',
                'a': 'Popular sandbars can be busy, especially on weekends. Private tours and early departures offer a more intimate experience.'
            },
            {
                'q': 'Can families with young kids go?',
                'a': 'Absolutely. The shallow water makes sandbars ideal for children. Life jackets available on all tours.'
            },
            {
                'q': 'What should I bring?',
                'a': 'Sunscreen, towel, sunglasses, and swimwear. Most tours provide shade, snacks, and non-alcoholic drinks. Bring a waterproof camera.'
            }
        ],
        'filter_func': lambda t: 'Boat Tour' in t.get('tags', []) and (t.get('duration') or 0) >= 120 and not any('Fishing' in tag or 'Dolphin' in tag for tag in t.get('tags', []))
    },
    {
        'filename': 'private-charters.html',
        'title': 'Private Boat Charters Key West',
        'slug': 'private-charters',
        'meta_desc': 'Private boat charters in Key West. Rent a boat for your group. Custom itineraries, fishing, snorkeling, celebrations.',
        'h1': 'Private Boat Charters Key West',
        'badge': 'Private Charters',
        'intro': """Create your perfect day on the water with a private boat charter. Whether you're planning a family outing, corporate event, wedding celebration, or adventure trip, a private charter gives you complete control over your itinerary and experience.

Charter boats range from 20-foot fishing vessels to 50-foot luxury catamarans. With captain and crew included, you can focus on relaxing and enjoying. Popular activities include snorkeling, fishing, exploring mangrove channels, swimming at sandbars, diving, and simply cruising. Many charters include food and beverage service.

Full-day and multi-day charters are available. Prices vary based on boat size, crew, and destination. Most charter companies require advance booking, especially during peak season. Perfect for special occasions, family reunions, or groups of 6-20+ people.""",
        'faq': [
            {
                'q': 'What\'s included in a private charter?',
                'a': 'Captain and crew, boat, fuel, and basic safety equipment. Many include snorkel gear, fishing equipment, and catering. Confirm what\'s included when booking.'
            },
            {
                'q': 'How many people fit on a charter?',
                'a': 'Depends on boat size. Small charters hold 4-6 people; large catamarans accommodate 20+. Capacity affects price.'
            },
            {
                'q': 'Can we customize our itinerary?',
                'a': 'Yes. That\'s the advantage of private charters. Work with your captain to plan snorkeling, fishing, beach visits, or island hopping.'
            },
            {
                'q': 'What\'s the minimum booking time?',
                'a': 'Most charters require 4-6 hours minimum. Full-day and multi-day options offer better per-hour rates.'
            }
        ],
        'filter_func': lambda t: 'Boat Rental' in t.get('tags', [])
    },
    {
        'filename': 'dolphin-tours.html',
        'title': 'Key West Dolphin Tours',
        'slug': 'dolphin-tours',
        'meta_desc': 'Dolphin watching tours in Key West. See wild dolphins in their natural habitat. Educational eco-tours, family-friendly.',
        'h1': 'Key West Dolphin Tours',
        'badge': 'Dolphin Encounters',
        'intro': """Swimming with or watching dolphins in their natural habitat is a magical Key West experience. These intelligent, playful marine mammals are found throughout the Keys and regularly spotted on dedicated dolphin tours.

Most dolphin tours operate in the shallow backcountry waters where dolphins hunt and play. Tours are led by experienced guides who understand dolphin behavior and ecology. You might see Atlantic bottlenose dolphins, spotted dolphins, or even the occasional spinner dolphin. Tours are respectful of marine life—guides follow strict distance and interaction guidelines.

Tours range from 2-4 hours and are suitable for all ages. Many combine dolphin watching with snorkeling, fishing, or sandbar visits. Best season is November through May, though dolphins are present year-round. Sightings are not guaranteed but highly likely on reputable tours.""",
        'faq': [
            {
                'q': 'Will we see dolphins for sure?',
                'a': 'Sightings are highly likely but not guaranteed. Guides know the best locations. If no dolphins are spotted, most operators offer partial refunds or rescheduling.'
            },
            {
                'q': 'Can we swim with the dolphins?',
                'a': 'No. Federal law prohibits dolphin interaction. Tours observe from boats only. This protects dolphins from stress and keeps them wild.'
            },
            {
                'q': 'What else happens on the tour?',
                'a': 'Many dolphin tours also include snorkeling, fishing, or time at sandbars. Some focus purely on dolphin watching and education.'
            },
            {
                'q': 'Are children allowed?',
                'a': 'Yes. Dolphin tours are family-friendly. Great educational opportunity for kids to learn about marine biology.'
            }
        ],
        'filter_func': lambda t: any('Dolphin' in tag for tag in t.get('tags', []))
    },
    {
        'filename': 'party-boats.html',
        'title': 'Key West Party Boats',
        'slug': 'party-boats',
        'meta_desc': 'Party boats and tiki boats in Key West. Bachelorette parties, bachelor parties, group celebrations with music and drinks.',
        'h1': 'Key West Party Boats',
        'badge': 'Party Cruises',
        'intro': """Key West party boats are the ultimate celebration experience—music, drinks, dancing, and friends all aboard. Whether it's a bachelor/bachelorette party, birthday bash, or group celebration, party boats combine cruise entertainment with social vibes.

Most party boats operate as "floating bars" with DJ, dancing, and open bar options. Food is typically included or available. Boats range from small (20-30 people) to large tiki boats (100+ capacity). Some focus on daytime party vibes; others are evening party cruises. Many operators offer themed cruises like "Tiki Bar Crawl" or "Sunset Party."

Tours typically last 2-4 hours. Group bookings often get discounts. Age restrictions apply (usually 21+ after 8 PM). Book in advance, especially for weekends and holidays. Perfect for celebrating milestones in true Key West style.""",
        'faq': [
            {
                'q': 'What\'s included in party boat tours?',
                'a': 'Varies by operator. Usually includes boat, DJ/music, and some basic amenities. Open bar/drinks may be extra. Confirm what\'s included.'
            },
            {
                'q': 'Is there a dress code?',
                'a': 'No strict dress code on most boats. Wear whatever\'s comfortable. Swimwear is fine. No shoes required on some tiki boats.'
            },
            {
                'q': 'How many people can fit?',
                'a': 'Small party boats hold 20-40. Large tiki boats accommodate 50-150+. Groups get custom quotes.'
            },
            {
                'q': 'Can we bring our own drinks?',
                'a': 'Most don\'t allow outside beverages. Purchase drinks onboard or book an "open bar" package.'
            }
        ],
        'filter_func': lambda t: any(keyword in t.get('name', '').lower() or keyword in t.get('description', '').lower() 
                                     for keyword in ['party', 'tiki', 'bar crawl', 'bachelorette', 'bachelor', 'celebration'])
    }
]

# Generate HTML pages
for page_config in pages:
    # Filter tours
    tours = [t for t in all_tours if page_config['filter_func'](t)]
    tours.sort(key=lambda t: t.get('price') or 0)  # Sort by price
    tours = tours[:12]  # Limit to 12 tours per page
    
    # Build tour cards HTML
    tour_cards = ""
    for i, tour in enumerate(tours, 1):
        price_html = f'<span class="tour-card-price">${tour.get("price", "Call")}</span>' if tour.get('price') else ''
        duration = tour.get('durationText', '').replace('Duration\n', '').strip()
        
        tour_cards += f'''                <!-- TOUR {i} -->
                <div class="tour-card">
                    <div class="tour-card-image" style="background-image: url('{tour.get("image", "")}')">
                        <span class="tour-card-badge">{tour.get('tags', ['Tour'])[0]}</span>
                        {price_html}
                    </div>
                    <div class="tour-card-content">
                        <div class="tour-card-company">{tour.get('company', 'Local Operator')}</div>
                        <h3>{tour.get('name', 'Tour')}</h3>
                        <div class="tour-card-meta"><span>⏱ {duration or 'Varies'}</span><span>👥 {tour.get('location', 'Key West').split('/')[-1]}</span></div>
                        <p class="tour-card-description">{tour.get('description', 'Experience the beauty of Key West.')[:120]}...</p>
                        <a href="{tour.get('bookingLink', '#')}" target="_blank" class="tour-card-cta" onclick="trackBookingClick('{tour.get('name', 'Tour')}', '{tour.get('id', '')}', {tour.get('price', 0) or 'null'})">Check Availability</a>
                    </div>
                </div>
                '''
    
    # Build FAQ HTML
    faq_html = ""
    for i, item in enumerate(page_config['faq'], 1):
        faq_html += f'''                <div class="faq-item">
                    <button class="faq-q" onclick="toggleFaq(event)">
                        <span>{item['q']}</span>
                        <span class="faq-toggle">+</span>
                    </button>
                    <div class="faq-a" style="display: none;">
                        {item['a']}
                    </div>
                </div>
                '''
    
    # Build breadcrumb schema
    breadcrumb_schema = f'''{{
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://keywestsandbartours.com/"}},
            {{"@type": "ListItem", "position": 2, "name": "{page_config['title']}", "item": "https://keywestsandbartours.com/{page_config['slug']}.html"}}
        ]
    }}'''
    
    # Build full HTML
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_config['title']} | Key West Sandbar Tours</title>
    <meta name="description" content="{page_config['meta_desc']}">
    <link rel="canonical" href="https://keywestsandbartours.com/{page_config['slug']}.html">
    <link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
    
    <!-- Open Graph -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://keywestsandbartours.com/{page_config['slug']}.html">
    <meta property="og:title" content="{page_config['title']}">
    <meta property="og:description" content="{page_config['meta_desc']}">
    <meta property="og:image" content="https://keywestsandbartours.com/og-image.jpg">
    
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap" rel="stylesheet">
    
    <!-- Schema -->
    <script type="application/ld+json">
    {breadcrumb_schema}
    </script>
    
    <!-- GA4 -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-67D7X60CJF"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', 'G-67D7X60CJF');
        
        function trackBookingClick(tourName, tourId, price) {{
            gtag('event', 'booking_click', {{
                'event_category': 'conversion',
                'event_label': tourName,
                'tour_id': tourId,
                'value': price,
                'page_type': '{page_config['slug']}'
            }});
        }}
    </script>
    
    <link rel="stylesheet" href="styles.css">
    <style>
        :root {{
            --sand: #F5E6D3;
            --ocean-deep: #0A3D62;
            --ocean-light: #1E90FF;
            --white: #FFFFFF;
            --off-white: #FAFAFA;
            --text-dark: #1A1A2E;
            --text-muted: #6B7280;
            --accent: #F59E0B;
        }}

        body {{ font-family: 'DM Sans', sans-serif; color: var(--text-dark); line-height: 1.6; }}
        .header {{ background: var(--white); padding: 16px 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header-inner {{ max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }}
        .logo {{ font-size: 1.1rem; font-weight: 700; color: var(--ocean-deep); text-decoration: none; display: flex; align-items: center; gap: 8px; }}
        .logo-img {{ width: 24px; height: 24px; }}
        
        .hero {{ background: linear-gradient(135deg, var(--ocean-deep) 0%, var(--ocean-light) 100%); color: var(--white); padding: 48px 20px; text-align: center; }}
        .hero h1 {{ font-family: 'Playfair Display', serif; font-size: 2.5rem; margin-bottom: 16px; }}
        .hero p {{ font-size: 1.1rem; margin-bottom: 24px; opacity: 0.95; }}
        .hero a {{ display: inline-block; background: var(--accent); color: var(--ocean-deep); padding: 14px 32px; border-radius: 50px; text-decoration: none; font-weight: 700; }}
        
        .intro {{ max-width: 1200px; margin: 0 auto; padding: 48px 20px; }}
        .intro h2 {{ font-family: 'Playfair Display', serif; font-size: 1.75rem; margin-bottom: 20px; }}
        .intro p {{ font-size: 1rem; line-height: 1.8; color: var(--text-muted); margin-bottom: 16px; }}
        
        .tours {{ background: var(--sand); padding: 48px 20px; }}
        .tours-inner {{ max-width: 1200px; margin: 0 auto; }}
        .section-label {{ display: inline-block; background: var(--accent); color: var(--ocean-deep); padding: 6px 14px; border-radius: 4px; font-size: 0.85rem; font-weight: 700; margin-bottom: 12px; }}
        .section-title {{ font-family: 'Playfair Display', serif; font-size: 1.75rem; margin-bottom: 32px; text-align: center; }}
        
        .tours-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
        .tour-card {{ background: var(--white); border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); transition: transform 0.3s, box-shadow 0.3s; }}
        .tour-card:hover {{ transform: translateY(-8px); box-shadow: 0 8px 20px rgba(0,0,0,0.15); }}
        .tour-card-image {{ height: 200px; background-size: cover; background-position: center; position: relative; }}
        .tour-card-badge, .tour-card-price {{ position: absolute; padding: 8px 14px; border-radius: 6px; font-size: 0.85rem; font-weight: 700; }}
        .tour-card-badge {{ top: 12px; left: 12px; background: var(--accent); color: var(--ocean-deep); }}
        .tour-card-price {{ top: 12px; right: 12px; background: var(--ocean-deep); color: var(--white); }}
        .tour-card-content {{ padding: 20px; }}
        .tour-card-company {{ font-size: 0.75rem; color: var(--ocean-light); font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }}
        .tour-card-content h3 {{ font-size: 1.1rem; color: var(--ocean-deep); margin-bottom: 8px; }}
        .tour-card-meta {{ display: flex; gap: 12px; margin-bottom: 12px; font-size: 0.85rem; color: var(--text-muted); }}
        .tour-card-description {{ font-size: 0.9rem; color: var(--text-muted); margin-bottom: 16px; }}
        .tour-card-cta {{ display: block; background: var(--accent); color: var(--ocean-deep); text-align: center; padding: 12px 16px; border-radius: 8px; text-decoration: none; font-weight: 700; }}
        .tour-card-cta:hover {{ background: #f3a500; }}
        
        .cta-box {{ background: var(--white); border-radius: 12px; padding: 32px 20px; text-align: center; margin: 32px 0; }}
        .cta-box h3 {{ font-size: 1.5rem; margin-bottom: 16px; }}
        .cta-box a {{ display: inline-block; background: var(--accent); color: var(--ocean-deep); padding: 14px 32px; border-radius: 50px; text-decoration: none; font-weight: 700; }}
        
        .faq {{ background: var(--off-white); padding: 48px 20px; }}
        .faq-inner {{ max-width: 1200px; margin: 0 auto; }}
        .faq h2 {{ font-family: 'Playfair Display', serif; font-size: 1.75rem; text-align: center; margin-bottom: 32px; }}
        .faq-item {{ background: var(--white); border-radius: 8px; margin-bottom: 12px; overflow: hidden; }}
        .faq-q {{ background: var(--sand); padding: 16px; border: none; cursor: pointer; display: flex; justify-content: space-between; align-items: center; width: 100%; font-size: 1rem; font-weight: 600; text-align: left; }}
        .faq-q:hover {{ background: #ede6d3; }}
        .faq-a {{ padding: 16px; background: var(--white); color: var(--text-muted); }}
        .faq-toggle {{ display: inline-block; width: 24px; text-align: center; }}
        
        .footer {{ background: var(--text-dark); color: var(--white); padding: 24px 20px; text-align: center; font-size: 0.9rem; }}
        .footer a {{ color: var(--accent); text-decoration: none; }}
        
        @media (max-width: 600px) {{
            .hero {{ padding: 32px 16px; }}
            .hero h1 {{ font-size: 1.75rem; }}
            .tours-grid {{ grid-template-columns: 1fr; }}
            .faq-q {{ padding: 14px; font-size: 0.95rem; }}
        }}
    </style>
</head>
<body>
    <!-- HEADER -->
    <header class="header">
        <div class="header-inner">
            <a href="/" class="logo">
                <img src="favicon-32.png" alt="" class="logo-img">
                Key West Sandbar Tours
            </a>
        </div>
    </header>
    
    <!-- HERO -->
    <section class="hero">
        <h1>{page_config['h1']}</h1>
        <p>{page_config['meta_desc']}</p>
        <a href="#tours-grid">Browse Tours</a>
    </section>
    
    <!-- INTRO -->
    <section class="intro">
        <h2>{page_config['h1']}</h2>
        <p>{page_config['intro']}</p>
    </section>
    
    <!-- TOURS -->
    <section class="tours">
        <div class="tours-inner">
            <div class="section-label">{page_config['badge']}</div>
            <h2 class="section-title">Available Tours</h2>
            
            <div id="tours-grid" class="tours-grid">
{tour_cards}            </div>
        </div>
    </section>
    
    <!-- CTA -->
    <div class="cta-box">
        <h3>Ready to Book?</h3>
        <p>Browse our tours above and secure your adventure in Key West.</p>
        <a href="#tours-grid">See Available Tours</a>
    </div>
    
    <!-- FAQ -->
    <section class="faq">
        <div class="faq-inner">
            <h2>Frequently Asked Questions</h2>
{faq_html}        </div>
    </section>
    
    <!-- FOOTER -->
    <footer class="footer">
        <p>&copy; 2026 Key West Sandbar Tours. All rights reserved. <a href="/">Home</a> | <a href="/about.html">About</a> | <a href="/faq.html">FAQs</a></p>
    </footer>
    
    <script>
        function toggleFaq(event) {{
            const item = event.target.closest('.faq-item');
            const answer = item.querySelector('.faq-a');
            const toggle = item.querySelector('.faq-toggle');
            
            answer.style.display = answer.style.display === 'none' ? 'block' : 'none';
            toggle.textContent = toggle.textContent === '+' ? '−' : '+';
        }}
    </script>
</body>
</html>'''
    
    # Write file
    with open(page_config['filename'], 'w') as f:
        f.write(html_content)
    
    print(f"✓ Created {page_config['filename']} ({len(tours)} tours)")

print("\nAll pages created successfully!")
