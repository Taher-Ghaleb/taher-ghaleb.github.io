(function () {
  'use strict';
  // Keep previously shared Team links working after the section was renamed.
  if (window.location.hash === '#students-section' && document.getElementById('team-section')) {
    window.history.replaceState(null, '', '#team-section');
  }
  // Re-align pasted fragment URLs after JSON-backed sections change page height.
  var pendingHash = window.location.hash;
  var userScrolled = false;
  function scrollTarget(target) {
    return target.matches('section') ? target.querySelector('h2.section-title') || target : target;
  }
  function alignHash() {
    if (!pendingHash || userScrolled || window.location.hash !== pendingHash) return;
    var id;
    try { id = decodeURIComponent(pendingHash.slice(1)); } catch (error) { return; }
    var target = document.getElementById(id);
    if (target) window.requestAnimationFrame(function () {
      if (!userScrolled && window.location.hash === pendingHash) scrollTarget(target).scrollIntoView({block: 'start', behavior: 'instant'});
    });
  }
  function stopFollowingHash() { userScrolled = true; }
  window.addEventListener('wheel', stopFollowingHash, {passive: true});
  window.addEventListener('touchstart', stopFollowingHash, {passive: true});
  document.addEventListener('keydown', function (event) {
    if (['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' '].includes(event.key)) stopFollowingHash();
  });
  window.addEventListener('hashchange', function () {
    pendingHash = window.location.hash;
    userScrolled = false;
    alignHash();
  });
  window.addEventListener('site:content-ready', alignHash);
  window.addEventListener('load', alignHash, {once: true});
  if (document.fonts) document.fonts.ready.then(alignHash);
  alignHash();
  document.addEventListener('click', function (event) {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    var link = event.target.closest('a[href]');
    if (!link || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
    var destination = new URL(link.href, window.location.href);
    function pagePath(pathname) { return pathname.replace(/\/index\.html$/, '/'); }
    if (!destination.hash || destination.origin !== window.location.origin || pagePath(destination.pathname) !== pagePath(window.location.pathname) || destination.search !== window.location.search) return;
    var id;
    try { id = decodeURIComponent(destination.hash.slice(1)); } catch (error) { return; }
    var target = document.getElementById(id);
    if (!target) return;
    event.preventDefault();
    if (window.location.hash !== destination.hash) window.history.pushState(null, '', destination.hash);
    pendingHash = destination.hash;
    userScrolled = false;
    scrollTarget(target).scrollIntoView({block: 'start', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
  });
  var header = document.querySelector('.standalone-navigation');
  if (!header) return;
  var toggle = header.querySelector('.navbar-toggler');
  var menu = header.querySelector('.navbar-collapse');
  function setMenu(open) {
    menu.classList.toggle('show', open);
    toggle.setAttribute('aria-expanded', String(open));
  }
  toggle.addEventListener('click', function () { setMenu(!menu.classList.contains('show')); });
  menu.addEventListener('click', function (event) {
    if (event.target.closest('a')) setMenu(false);
  });
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && menu.classList.contains('show')) {
      setMenu(false);
      toggle.focus();
    }
  });
  function updateHeader() { header.classList.toggle('scrolled', window.scrollY > 40); }
  window.addEventListener('scroll', updateHeader, {passive: true});
  updateHeader();
})();
