/* ============================================
   KeyWestSandbarTours — booking_click tracking
   ============================================
   Single source of truth for the booking_click GA4 conversion event.
   Loaded site-wide via <script src="/tracking.js" defer> in <head>.

   Wires every Check Availability anchor (FareHarbor links and CTA-class
   anchors) via document-level click delegation — no per-anchor onclick
   required. Survives runtime-rendered anchors.

   Coexistence notes:
   - Anchors with an existing onclick="trackBookingClick(...)" are skipped
     so they do not double-fire (the audit shows 125 such anchors already
     wired across landing pages).
   - Each KWST page defines its own inline trackBookingClick(...) in <head>
     with varying signatures (homepage uses (tourName, tourId, area),
     snorkeling uses (tourName, tourId, price), dolphin-tours-key-west
     uses (location)). This file's window.trackBookingClick fallback is
     only set when no function is already defined, so existing per-page
     definitions keep winning. The delegated handler below fires gtag
     directly with the canonical 3-arg field shape.

   utm_source tagging:
   - On every FareHarbor link click, we append utm_source=keywestsandbartours
     so GA4 can attribute the booking to KWST.
   - appendUtmSource is a vendored copy of _tools/generators/source-tag.js
     (_tools PR #84, 4e73885). Inlined here instead of loaded as a
     separate <script> to avoid editing every page <head>.
*/

(function () {
    function appendUtmSource(url, slug) {
        if (typeof url !== 'string' || !url) return url;
        if (typeof slug !== 'string' || !slug) return url;
        if (url.indexOf('fareharbor.com') === -1) return url;
        if (/[?&]utm_source=/.test(url)) return url;
        var sep = url.indexOf('?') === -1 ? '?' : '&';
        return url + sep + 'utm_source=' + encodeURIComponent(slug);
    }

    var CTA_CLASSES = [
        'book-btn',
        'book-btn-inline',
        'btn-primary',
        'tour-book-btn',
        'tour-card-cta',
        'pick-card-cta',
        'cta-btn',
        'cta-button',
        'final-cta-btn',
        'browse-cta-btn',
        'mobile-cta-btn',
        'mobile-cta',
        'primary-cta',
        'island-cta',
        'area-card',
        'footer-cta',
        'sidebar-cta',
        'blog-cta',
        'tour-cta',
        'check-availability'
    ];

    var REGION_KEYWORDS = ['key-west', 'marathon', 'key-largo', 'islamorada', 'stock-island', 'lower-keys', 'big-pine', 'dry-tortugas'];

    function detectArea() {
        var path = (location && location.pathname) || '';
        for (var i = 0; i < REGION_KEYWORDS.length; i++) {
            if (path.indexOf(REGION_KEYWORDS[i]) !== -1) return REGION_KEYWORDS[i];
        }
        return 'florida-keys';
    }

    function readContext(link) {
        var href = link.getAttribute('href') || '';
        var name = link.dataset.tourName
            || link.textContent.replace(/[→➤➔\s]+$/, '').trim()
            || 'unknown';
        var id = link.dataset.tourId || href || 'unknown';
        return { name: name, id: id, href: href };
    }

    if (typeof window.trackBookingClick !== 'function') {
        window.trackBookingClick = function (tourName, tourId, area) {
            if (typeof gtag === 'undefined') return;
            gtag('event', 'booking_click', {
                event_category: 'conversion',
                event_label: tourName,
                tour_name: tourName,
                tour_id: tourId,
                area: area || detectArea()
            });
        };
    }

    function hasCtaClass(link) {
        if (!link.classList) return false;
        for (var i = 0; i < CTA_CLASSES.length; i++) {
            if (link.classList.contains(CTA_CLASSES[i])) return true;
        }
        return false;
    }

    document.addEventListener('click', function (e) {
        var link = e.target.closest && e.target.closest('a');
        if (!link) return;
        var href = link.getAttribute('href') || '';
        var isFareHarbor = href.indexOf('fareharbor.com') !== -1;
        // utm_source rewrite runs BEFORE the onclick-skip below, because
        // KWST's app.js renders FH anchors with onclick="trackBookingClickEnhanced(...)"
        // and the substring-match skip would otherwise short-circuit the rewrite.
        // The rewrite is orthogonal to gtag firing — tag the URL either way.
        if (isFareHarbor) {
            link.href = appendUtmSource(link.href, 'keywestsandbartours');
        }
        var onclickAttr = link.getAttribute('onclick') || '';
        if (onclickAttr.indexOf('trackBookingClick') !== -1) return;
        if (!isFareHarbor && !hasCtaClass(link)) return;
        var ctx = readContext(link);
        if (typeof gtag === 'undefined') return;
        gtag('event', 'booking_click', {
            event_category: 'conversion',
            event_label: ctx.name,
            tour_name: ctx.name,
            tour_id: ctx.id,
            area: detectArea()
        });
    });
})();
