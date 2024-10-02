(function () {
  'use strict';
  var photoFiles = new Map();
  function loadPhotoIndex() {
    // GitHub Pages builds this list from the actual filenames via Jekyll.
    return fetch('team/photo-index.json').then(function (response) {
      if (!response.ok) throw new Error('Photo index unavailable');
      return response.json();
    }).then(function (index) { return index.files || []; }).catch(function () {
      // Python's local preview serves directory listings instead of building Liquid.
      return fetch('team/photos/').then(function (response) {
        if (!response.ok) return [];
        return response.text().then(function (html) {
          var directory = new DOMParser().parseFromString(html, 'text/html');
          return Array.from(directory.querySelectorAll('a[href]')).map(function (link) {
            return decodeURIComponent(link.getAttribute('href'));
          }).filter(function (name) { return !name.includes('/') && /\.(jpe?g|png|webp|gif|avif|svg)$/i.test(name); });
        });
      }).catch(function () { return []; });
    });
  }
  function element(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function monthLabel(value, fallback) {
    if (!value || !/^\d{4}-(0[1-9]|1[0-2])$/.test(value)) return fallback;
    var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return months[Number(value.slice(5)) - 1] + ' ' + value.slice(0, 4);
  }
  function isPlaceholder(filename) { return /^placeholder(?:[-.])/i.test(filename); }
  function photoSelection(member) {
    function basename(value) { return String(value || '').split(/[\\/]/).pop(); }
    var configured = basename(member.photo);
    var fallback = basename(member.placeholderPhoto) || (isPlaceholder(configured) ? configured : 'placeholder.svg');
    fallback = photoFiles.get(fallback.toLowerCase()) || fallback;
    if (configured && !isPlaceholder(configured) && photoFiles.has(configured.toLowerCase())) {
      return {filename: photoFiles.get(configured.toLowerCase()), fallback: fallback};
    }
    var name = String(member.name || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    var stems = [name, String(member.id || '').toLowerCase()];
    var extensions = ['webp', 'jpg', 'jpeg', 'png', 'avif', 'gif', 'svg'];
    for (var i = 0; i < stems.length; i++) {
      if (!stems[i]) continue;
      for (var j = 0; j < extensions.length; j++) {
        var match = photoFiles.get(stems[i] + '.' + extensions[j]);
        if (match) return {filename: match, fallback: fallback};
      }
    }
    return {filename: configured && !isPlaceholder(configured) && !photoFiles.size ? configured : fallback, fallback: fallback};
  }
  function memberCard(member, headingTag) {
    var card = element('article', 'member-card');
    if (member.placeholder) card.appendChild(element('span', 'member-placeholder', 'Placeholder profile'));
    var frame = element('div', 'member-photo');
    var photo = element('img');
    var selection = photoSelection(member);
    var filename = selection.filename;
    photo.src = 'team/photos/' + encodeURIComponent(filename);
    photo.alt = member.placeholder ? '' : (isPlaceholder(filename) ? 'Placeholder portrait for ' : 'Portrait of ') + member.name;
    photo.width = 160;
    photo.height = 160;
    photo.loading = 'lazy';
    photo.decoding = 'async';
    photo.style.objectPosition = member.photoPosition || 'center';
    photo.addEventListener('error', function () {
      photo.alt = member.placeholder ? '' : 'Placeholder portrait for ' + member.name;
      photo.src = 'team/photos/' + encodeURIComponent(selection.fallback);
    }, {once: true});
    frame.appendChild(photo);
    card.appendChild(frame);
    card.appendChild(element(headingTag || 'h3', 'member-name', member.name));
    if (member.role) card.appendChild(element('p', 'member-role', member.role));
    var university = member.university || {};
    var universityBadge = element('p', 'member-university');
    if (university.accent === 'green' || university.accent === 'red') {
      universityBadge.classList.add('member-university-' + university.accent);
    }
    universityBadge.title = university.name || 'University to be added';
    var universityIcon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    universityIcon.setAttribute('viewBox', '0 0 24 24');
    universityIcon.setAttribute('fill', 'none');
    universityIcon.setAttribute('stroke', 'currentColor');
    universityIcon.setAttribute('stroke-width', '1.6');
    universityIcon.setAttribute('aria-hidden', 'true');
    var universityShape = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    universityShape.setAttribute('d', 'M2 9l10-6 10 6H2zm3 3v7m5-7v7m4-7v7m5-7v7M2 22h20');
    universityIcon.appendChild(universityShape);
    universityBadge.appendChild(universityIcon);
    universityBadge.appendChild(document.createTextNode(university.shortName || university.name || 'University to be added'));
    card.appendChild(universityBadge);
    var topics = element('ul', 'member-topics');
    topics.setAttribute('aria-label', 'Research topics');
    (member.topics || []).forEach(function (topic) { topics.appendChild(element('li', '', topic)); });
    card.appendChild(topics);
    var dates = element('p', 'member-dates');
    var icon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    icon.setAttribute('viewBox', '0 0 24 24');
    icon.setAttribute('fill', 'none');
    icon.setAttribute('stroke', 'currentColor');
    icon.setAttribute('stroke-width', '1.7');
    icon.setAttribute('aria-hidden', 'true');
    var shape = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    shape.setAttribute('d', 'M4 5h16v16H4V5zm3-3v6m10-6v6M4 10h16');
    icon.appendChild(shape);
    dates.appendChild(icon);
    var start = monthLabel(member.startDate, member.placeholder ? 'Start date' : 'Start date to be added');
    var end = monthLabel(member.endDate, member.placeholder ? 'End date' : member.status === 'alumni' ? 'End date to be added' : 'Present');
    var startNode = element(member.startDate ? 'time' : 'span', '', start);
    var endNode = element(member.endDate ? 'time' : 'span', '', end);
    if (member.startDate) startNode.dateTime = member.startDate;
    if (member.endDate) endNode.dateTime = member.endDate;
    dates.appendChild(startNode);
    dates.appendChild(document.createTextNode(' – '));
    dates.appendChild(endNode);
    card.appendChild(dates);
    return card;
  }
  function carousel(container, members) {
    members.forEach(function (member) { container.appendChild(memberCard(member)); });
    if (!members.length) {
      container.appendChild(element('p', 'members-empty', 'Member details will be added soon.'));
      return;
    }
    var $ = window.jQuery;
    if (!$ || !$.fn.owlCarousel || members.length === 1) return;
    var slider = $(container);
    var region = document.getElementById('members-home-panel');
    var controls = element('div', 'members-controls');
    var previous = element('button', '', '← Previous');
    var pause = element('button', '', 'Pause rotation');
    var next = element('button', '', 'Next →');
    var position = element('span', 'members-position');
    [previous, pause, next].forEach(function (button) {
      button.type = 'button';
      button.setAttribute('aria-controls', container.id);
      controls.appendChild(button);
    });
    region.appendChild(controls);
    region.appendChild(position);
    container.classList.add('owl-carousel');
    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    var paused = reducedMotion.matches;
    slider.on('initialized.owl.carousel changed.owl.carousel refreshed.owl.carousel', function (event) {
      if (!event.item || event.item.index == null) return;
      var current = event.relatedTarget.relative(event.item.index) + 1;
      position.textContent = current + ' / ' + members.length;
      position.setAttribute('aria-label', 'Member carousel position ' + current + ' of ' + members.length);
    });
    slider.on('initialized.owl.carousel translated.owl.carousel refreshed.owl.carousel', function () {
      slider.find('.owl-item').each(function () {
        this.setAttribute('aria-hidden', this.classList.contains('active') ? 'false' : 'true');
      });
    });
    slider.owlCarousel({
      items: 3, loop: true, margin: 18, nav: false, dots: false,
      autoplay: !paused, autoplayTimeout: 7000, autoplaySpeed: 700,
      autoplayHoverPause: false, smartSpeed: 700,
      responsive: {0: {items: 1}, 600: {items: 2}, 992: {items: 3}}
    });
    function playback() {
      pause.textContent = paused ? 'Resume rotation' : 'Pause rotation';
      if (paused || document.hidden || region.matches(':hover') || region.contains(document.activeElement)) {
        slider.trigger('stop.owl.autoplay');
      } else {
        slider.trigger('play.owl.autoplay', [7000]);
      }
    }
    previous.addEventListener('click', function () { slider.trigger('prev.owl.carousel', [reducedMotion.matches ? 0 : 700]); });
    next.addEventListener('click', function () { slider.trigger('next.owl.carousel', [reducedMotion.matches ? 0 : 700]); });
    pause.addEventListener('click', function () { paused = !paused; playback(); });
    region.addEventListener('mouseenter', playback);
    region.addEventListener('mouseleave', playback);
    region.addEventListener('focusin', playback);
    region.addEventListener('focusout', function () { setTimeout(playback, 0); });
    document.addEventListener('visibilitychange', playback);
    playback();
  }
  function render(data) {
    // JSON order breaks ties, preserving the user's ordering for equal start dates.
    var members = (data.members || []).map(function (member, index) {
      return {member: member, order: index};
    }).sort(function (a, b) {
      return String(b.member.startDate || '').localeCompare(String(a.member.startDate || '')) || a.order - b.order;
    }).map(function (item) { return item.member; });
    var current = members.filter(function (member) { return member.status !== 'alumni'; });
    var alumni = members.filter(function (member) { return member.status === 'alumni'; });
    var home = document.getElementById('members-home');
    if (home) carousel(home, current);
    var list = document.getElementById('members-current');
    if (list) {
      function renderCategories(target, group) {
        (data.categories || []).forEach(function (category) {
          var categoryMembers = group.filter(function (member) { return member.category === category.id; });
          if (!categoryMembers.length) return;
          var section = element('section', 'member-category');
          var heading = element('h3', 'member-category-title');
          heading.id = target.id + '-' + category.id;
          var categoryLink = element('a', 'member-category-link', category.label);
          categoryLink.href = '#' + heading.id;
          categoryLink.title = 'Direct link to ' + category.label;
          heading.appendChild(categoryLink);
          section.setAttribute('aria-labelledby', heading.id);
          section.appendChild(heading);
          var grid = element('div', 'members-grid');
          categoryMembers.forEach(function (member) { grid.appendChild(memberCard(member, 'h4')); });
          section.appendChild(grid);
          target.appendChild(section);
        });
        if (!group.length) target.appendChild(element('p', 'members-empty', 'Member details will be added soon.'));
      }
      renderCategories(list, current);
      var alumniSection = document.getElementById('members-alumni-section');
      alumniSection.hidden = !alumni.length;
      renderCategories(document.getElementById('members-alumni'), alumni);
    }
    document.querySelectorAll('[data-members-placeholder-notice]').forEach(function (notice) {
      notice.hidden = !members.some(function (member) { return member.placeholder; });
    });
  }
  var membersRequest = fetch('team/members.json').then(function (response) {
    if (!response.ok) throw new Error('HTTP ' + response.status);
    return response.json();
  });
  Promise.all([membersRequest, loadPhotoIndex()]).then(function (results) {
    results[1].forEach(function (filename) { photoFiles.set(filename.toLowerCase(), filename); });
    render(results[0]);
  }).catch(function (error) {
    console.error('Failed to load members:', error);
    var target = document.getElementById('members-home') || document.getElementById('members-current');
    if (target) target.textContent = 'Member profiles could not be loaded. Please refresh the page.';
  }).then(function () {
    window.dispatchEvent(new Event('site:content-ready'));
  });
})();
