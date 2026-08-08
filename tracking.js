/* ============================================
   KeyWestSandbarTours — booking_click tracking
   ============================================
   Single source of truth for the booking_click GA4 conversion event.
   Loaded site-wide via <script src="/tracking.js" defer> in <head>.

   Wires every FareHarbor booking anchor via document-level click
   delegation — no per-anchor onclick required. Survives runtime-rendered
   anchors. Firing requires a fareharbor.com href; CSS classes alone never
   fire booking_click (a prior CTA-class heuristic false-positived on 44
   internal navigation links that reused booking-button styling classes,
   and was removed).

   Coexistence notes:
   - Anchors with an existing onclick containing "trackBookingClick" are
     skipped so they do not double-fire. Two such anchors exist today:
     app.js's rendered tour cards (trackBookingClickEnhanced) and the
     sandbar-charter-quiz results (trackBookingClickQuiz) — both fire
     gtag('booking_click', ...) themselves with richer context than this
     file's generic fallback provides.
   - This file's window.trackBookingClick fallback is only set when no
     function is already defined by that exact name.

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
        // Never fall back to link.textContent: an unattributed CTA would report
        // its button label ("Check Availability"), collapsing every unattributed
        // click into one GA4 row. 'unknown' keeps the gap visible instead.
        var name = link.dataset.tourName || 'unknown';
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
        if (!isFareHarbor) return;
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
