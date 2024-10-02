(function () {
  'use strict';
  var $ = window.jQuery;
  if (!$ || !$.fn.owlCarousel) return;
  var carousel = $('#courses-carousel');
  if (!carousel.length) return;
  var region = document.querySelector('.courses-panel');
  var pause = document.getElementById('courses-pause');
  var position = document.getElementById('courses-position');
  var total = carousel.children().length;
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var paused = reducedMotion.matches;
  carousel.on('initialized.owl.carousel changed.owl.carousel refreshed.owl.carousel', function (event) {
    if (!event.item || event.item.index == null) return;
    var start = event.relatedTarget.relative(event.item.index);
    var visible = event.relatedTarget.settings.items;
    var numbers = [];
    for (var i = 0; i < visible; i++) numbers.push((start + i) % total + 1);
    position.textContent = 'Course' + (visible > 1 ? 's ' : ' ') + numbers.join(' & ') + ' of ' + total;
  });
  carousel.on('initialized.owl.carousel translated.owl.carousel refreshed.owl.carousel', function () {
    carousel.find('.owl-item').each(function () {
      this.setAttribute('aria-hidden', this.classList.contains('active') ? 'false' : 'true');
    });
  });
  carousel.owlCarousel({
    items: 2, loop: true, margin: 20, nav: false, dots: false,
    autoplay: !paused, autoplayTimeout: 7000, autoplaySpeed: 700,
    autoplayHoverPause: false, smartSpeed: 700,
    responsive: {0: {items: 1}, 768: {items: 2}}
  });
  function playback() {
    pause.textContent = paused ? 'Resume' : 'Pause';
    pause.setAttribute('aria-label', paused ? 'Resume course rotation' : 'Pause course rotation');
    if (paused || document.hidden || region.matches(':hover') || region.contains(document.activeElement)) {
      carousel.trigger('stop.owl.autoplay');
    } else {
      carousel.trigger('play.owl.autoplay', [7000]);
    }
  }
  document.getElementById('courses-previous').addEventListener('click', function () {
    carousel.trigger('prev.owl.carousel', [reducedMotion.matches ? 0 : 700]);
  });
  document.getElementById('courses-next').addEventListener('click', function () {
    carousel.trigger('next.owl.carousel', [reducedMotion.matches ? 0 : 700]);
  });
  pause.addEventListener('click', function () { paused = !paused; playback(); });
  region.addEventListener('mouseenter', playback);
  region.addEventListener('mouseleave', playback);
  region.addEventListener('focusin', playback);
  region.addEventListener('focusout', function () { setTimeout(playback, 0); });
  document.addEventListener('visibilitychange', playback);
  playback();
})();
