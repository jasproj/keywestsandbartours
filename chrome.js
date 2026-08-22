/* Shared chrome behaviour. The header itself is server-delivered HTML — this
   only wires the mobile menu, so a crawler with no JS still gets the full nav.
   Generated alongside the markup by tools/build-chrome.py. */
(function () {
  var btn = document.querySelector('.site-nav-toggle');
  var nav = document.getElementById('site-nav-mobile');
  if (!btn || !nav) return;
  btn.addEventListener('click', function () {
    var open = nav.classList.toggle('is-open');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
})();
