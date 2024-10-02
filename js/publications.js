(function () {
  'use strict';
  // Inline icons keep publication metadata visible without a third-party icon font.
  var icons = {
    journal: 'M12 5C9 3 5 3 2 4v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1zm0 0v15',
    conference: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2m20 0v-2a4 4 0 0 0-3-3.87M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm7 0a4 4 0 0 1 0 8',
    workshop: 'M14.7 6.3a5 5 0 0 0-6.4 6.4L2 19l3 3 6.3-6.3a5 5 0 0 0 6.4-6.4L14 13l-3-3 3.7-3.7z',
    patent: 'M8 3h8l5 5v13H3V3h5zm8 0v5h5M7 12h10M7 16h7',
    venue: 'M2 9l10-6 10 6H2zm3 3v7m5-7v7m4-7v7m5-7v7M2 22h20',
    year: 'M4 5h16v16H4V5zm3-3v6m10-6v6M4 10h16m-12 4h1m3 0h1m3 0h1m-9 4h1m3 0h1',
    topic: 'M3 3h8l10 10-8 8L3 11V3zm5 4h.01',
    doi: 'M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-2 2m3 6a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l2-2'
  };
  function element(tag, className, text) {
    var el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  }
  function badge(icon, text) {
    var el = element('span', 'publication-badge');
    var glyph = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    glyph.setAttribute('viewBox', '0 0 24 24');
    glyph.setAttribute('width', '15');
    glyph.setAttribute('height', '15');
    glyph.setAttribute('fill', 'none');
    glyph.setAttribute('stroke', 'currentColor');
    glyph.setAttribute('stroke-width', '1.7');
    glyph.setAttribute('stroke-linecap', 'round');
    glyph.setAttribute('stroke-linejoin', 'round');
    glyph.setAttribute('aria-hidden', 'true');
    var shape = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    shape.setAttribute('d', icons[icon] || icons.conference);
    glyph.appendChild(shape);
    el.appendChild(glyph);
    el.appendChild(document.createTextNode(' ' + text));
    return el;
  }
  function entry(pub) {
    var article = element('article', 'publication-entry');
    article.id = pub.id;
    var topics = element('div', 'publication-topics');
    (pub.topics || []).forEach(function (topic) { topics.appendChild(badge('topic', topic)); });
    article.appendChild(topics);
    article.appendChild(element('h3', 'publication-title', pub.title));
    var authors = element('p', 'publication-authors');
    pub.authors.forEach(function (author, index) {
      if (index) authors.appendChild(document.createTextNode(', '));
      authors.appendChild(element(author.self ? 'strong' : 'span', '', author.name));
    });
    article.appendChild(authors);
    var meta = element('div', 'publication-meta');
    var type = pub.type || 'conference';
    meta.appendChild(badge(type, type.charAt(0).toUpperCase() + type.slice(1)));
    var venue = badge('venue', pub.venueName || pub.venue);
    venue.title = pub.venueFullName ? pub.venueFullName + (pub.year ? ' (' + pub.year + ')' : '') : pub.venue;
    meta.appendChild(venue);
    meta.appendChild(badge('year', pub.year));
    if (pub.doi) {
      var doiLink = element('a', 'publication-doi');
      doiLink.href = 'https://doi.org/' + pub.doi;
      doiLink.target = '_blank';
      doiLink.rel = 'noopener';
      var preprint = pub.doiType === 'preprint';
      doiLink.title = (preprint ? 'Open arXiv preprint: ' : 'Open paper: ') + pub.doi;
      doiLink.setAttribute('aria-label', (preprint ? 'Open arXiv preprint for ' : 'Open DOI page for ') + pub.title);
      doiLink.appendChild(badge('doi', preprint ? 'DOI (arXiv)' : 'DOI'));
      meta.appendChild(doiLink);
    }
    article.appendChild(meta);
    if (type === 'patent') article.appendChild(element('p', 'publication-patent', pub.venue));
    return article;
  }
  function featuredCarousel(container, papers) {
    var $ = window.jQuery;
    if (!$ || !$.fn.owlCarousel || papers.length <= 4) {
      papers.forEach(function (pub) { container.appendChild(entry(pub)); });
      return;
    }
    // Each slide is a complete page of four papers in a 2×2 grid.
    container.classList.add('owl-carousel');
    for (var i = 0; i < papers.length; i += 4) {
      var column = element('div', 'featured-publication-page');
      papers.slice(i, i + 4).forEach(function (pub) {
        var card = entry(pub);
        card.removeAttribute('id'); // Owl duplicates columns to make the loop seamless.
        column.appendChild(card);
      });
      container.appendChild(column);
    }
    var carousel = $(container);
    var region = document.getElementById('featured-publications-carousel');
    var controls = element('div', 'featured-carousel-controls');
    var previous = element('button', '', '← Previous');
    var pause = element('button', '', 'Pause rotation');
    var next = element('button', '', 'Next →');
    var position = element('span', 'featured-carousel-position');
    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    var paused = reducedMotion.matches;
    [previous, pause, next].forEach(function (button) {
      button.type = 'button';
      button.setAttribute('aria-controls', container.id);
      controls.appendChild(button);
    });
    region.appendChild(controls);
    region.appendChild(position);
    function updatePosition(event) {
      if (!event.item || event.item.index == null) return;
      var current = event.relatedTarget.relative(event.item.index) + 1;
      position.textContent = current + ' / ' + event.item.count;
      position.setAttribute('aria-label', 'Publication page ' + current + ' of ' + event.item.count);
    }
    carousel.on('initialized.owl.carousel changed.owl.carousel refreshed.owl.carousel', updatePosition);
    function playback() {
      pause.textContent = paused ? 'Resume rotation' : 'Pause rotation';
      if (paused || document.hidden || region.matches(':hover') || region.contains(document.activeElement)) {
        carousel.trigger('stop.owl.autoplay');
      } else {
        carousel.trigger('play.owl.autoplay', [7000]);
      }
    }
    carousel.on('initialized.owl.carousel translated.owl.carousel refreshed.owl.carousel', function () {
      carousel.find('.owl-item').each(function () {
        this.setAttribute('aria-hidden', this.classList.contains('active') ? 'false' : 'true');
      });
    });
    carousel.owlCarousel({
      items: 1, loop: true, margin: 18, dots: false, nav: false,
      autoplay: !paused, autoplayTimeout: 7000, autoplaySpeed: 800,
      smartSpeed: 800, autoplayHoverPause: false
    });
    previous.addEventListener('click', function () { carousel.trigger('prev.owl.carousel', [reducedMotion.matches ? 0 : 800]); });
    next.addEventListener('click', function () { carousel.trigger('next.owl.carousel', [reducedMotion.matches ? 0 : 800]); });
    pause.addEventListener('click', function () { paused = !paused; playback(); });
    region.addEventListener('mouseenter', playback);
    region.addEventListener('mouseleave', playback);
    region.addEventListener('focusin', playback);
    region.addEventListener('focusout', function () { setTimeout(playback, 0); });
    document.addEventListener('visibilitychange', playback);
    playback();
  }
  function init(data) {
    var papers = data.journal.concat(data.conference).sort(function (a, b) { return b.year - a.year || a.title.localeCompare(b.title); });
    var featured = document.getElementById('featured-publications');
    if (featured) {
      var featuredPapers = papers.filter(function (pub) { return pub.featuredTopic; })
        .sort(function (a, b) { return a.featuredOrder - b.featuredOrder; });
      featuredCarousel(featured, featuredPapers.concat(papers.filter(function (pub) { return !pub.featuredTopic; })));
    }
    var list = document.getElementById('all-publications');
    if (!list) return;
    var all = papers.concat(data.patent);
    var search = document.getElementById('publication-search');
    var topic = document.getElementById('publication-topic');
    var year = document.getElementById('publication-year');
    var venue = document.getElementById('publication-venue');
    var status = document.getElementById('publication-status');
    var previous = document.querySelectorAll('[data-publication-previous]');
    var next = document.querySelectorAll('[data-publication-next]');
    var pageStatus = document.querySelectorAll('[data-publication-page]');
    var patents = document.getElementById('publication-patents');
    var patentSection = document.getElementById('patents-section');
    var patentSummary = document.getElementById('patent-summary');
    var page = 0, pageSize = 10;
    function options(select, values, numeric) {
      Array.from(new Set(values)).filter(Boolean).sort(function (a, b) {
        return numeric ? b - a : a.localeCompare(b);
      }).forEach(function (value) { var option = element('option', '', value); option.value = value; select.appendChild(option); });
    }
    options(topic, papers.reduce(function (topics, pub) { return topics.concat(pub.topics || []); }, []));
    options(year, all.map(function (pub) { return pub.year; }), true);
    options(venue, all.map(function (pub) { return pub.venueName || pub.venue; }));
    function matches(pub) {
      var query = search.value.trim().toLowerCase();
      var text = [pub.title, pub.venueName || '', pub.venue, pub.venueFullName || '', pub.year].concat(pub.topics || [], pub.authors.map(function (author) { return author.name; })).join(' ').toLowerCase();
      return (!query || text.includes(query)) && (!topic.value || (pub.topics || []).includes(topic.value)) &&
        (!year.value || String(pub.year) === year.value) && (!venue.value || (pub.venueName || pub.venue) === venue.value);
    }
    function render() {
      var results = papers.filter(matches), patentResults = data.patent.filter(matches);
      var pages = Math.max(1, Math.ceil(results.length / pageSize));
      page = Math.min(page, pages - 1);
      list.replaceChildren();
      results.slice(page * pageSize, (page + 1) * pageSize).forEach(function (pub) { list.appendChild(entry(pub)); });
      if (!results.length) list.appendChild(element('p', 'publication-empty', 'No papers match these filters. Try another search or clear the filters.'));
      status.textContent = results.length + (results.length === 1 ? ' paper' : ' papers') + ' · ' + patentResults.length + (patentResults.length === 1 ? ' patent' : ' patents');
      pageStatus.forEach(function (status) { status.textContent = results.length ? (page * pageSize + 1) + '–' + Math.min((page + 1) * pageSize, results.length) + ' of ' + results.length + ' papers' : '0 papers'; });
      previous.forEach(function (button) { button.disabled = page === 0; });
      next.forEach(function (button) { button.disabled = page >= pages - 1; });
      patents.replaceChildren();
      patentResults.forEach(function (pub) { patents.appendChild(entry(pub)); });
      patentSummary.textContent = 'Granted US patents (' + patentResults.length + ')';
      patentSection.hidden = !patentResults.length;
    }
    [search, topic, year, venue].forEach(function (control) {
      control.addEventListener(control === search ? 'input' : 'change', function () { page = 0; render(); });
    });
    document.getElementById('publication-reset').addEventListener('click', function () {
      [search, topic, year, venue].forEach(function (control) { control.value = ''; });
      page = 0; render(); search.focus();
    });
    function changePage(delta) {
      page += delta; render(); list.focus();
      document.getElementById('publication-pagination-top').scrollIntoView({block: 'start', behavior: 'smooth'});
    }
    previous.forEach(function (button) { button.addEventListener('click', function () { changePage(-1); }); });
    next.forEach(function (button) { button.addEventListener('click', function () { changePage(1); }); });
    render();
  }
  fetch('papers/publications.json').then(function (response) {
    if (!response.ok) throw new Error('HTTP ' + response.status);
    return response.json();
  }).then(init).catch(function (error) {
    console.error('Failed to load publications:', error);
    var target = document.getElementById('featured-publications') || document.getElementById('all-publications');
    if (target) target.textContent = 'Publications could not be loaded. Please refresh the page or visit my Google Scholar profile.';
  }).then(function () {
    window.dispatchEvent(new Event('site:content-ready'));
  });
})();
