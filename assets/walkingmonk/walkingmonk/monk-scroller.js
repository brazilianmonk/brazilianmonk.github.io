/**
 * Monk Scroller — a bottom-fixed scroll-progress bar with an animated monk
 * as the draggable thumb. He walks while you scroll, and settles into
 * meditation when the page is still.
 *
 * Integration:
 *   1. Copy the `images/` folder, monk-scroller.css and monk-scroller.js
 *      next to your page (or anywhere reachable).
 *   2. In your HTML:
 *        <link rel="stylesheet" href="monk-scroller.css">
 *        <script src="monk-scroller.js"></script>
 *   3. That's it — it self-initializes on DOMContentLoaded.
 *
 * Optional config (set before the script loads):
 *   window.MonkScrollerConfig = { imageBase: 'images/', idleDelay: 700 };
 */
(function () {
  'use strict';

  var config = window.MonkScrollerConfig || {};
  var IMAGE_BASE = config.imageBase || 'images/';
  var IDLE_DELAY = config.idleDelay || 700; // ms of no scroll before meditating
  var WALK_FRAME_MS = config.walkFrameMs || 140;
  var MEDITATE_FRAME_MS = config.meditateFrameMs || 650;

  var FRAMES = {
    walk: [
      IMAGE_BASE + 'walk1.svg',
      IMAGE_BASE + 'walk2.svg',
      IMAGE_BASE + 'walk3.svg',
      IMAGE_BASE + 'walk4.svg'
    ],
    meditate: [IMAGE_BASE + 'meditate1.svg', IMAGE_BASE + 'meditate2.svg']
  };

  function init() {
    var track = document.createElement('div');
    track.id = 'monk-scroller-track';

    var thumb = document.createElement('div');
    thumb.id = 'monk-scroller-thumb';
    thumb.setAttribute('role', 'scrollbar');
    thumb.setAttribute('aria-label', 'Page scroll position — drag the monk to scroll');
    thumb.tabIndex = 0;

    var hint = document.createElement('div');
    hint.className = 'monk-scroller-hint';
    hint.textContent = 'drag me';
    thumb.appendChild(hint);

    var img = document.createElement('img');
    img.alt = 'Walking, meditating monk used as a scroll handle';
    img.src = FRAMES.meditate[0];
    thumb.appendChild(img);

    track.appendChild(thumb);
    document.body.appendChild(track);

    var state = 'idle'; // 'idle' | 'walking' | 'meditating'
    var frameIndex = 0;
    var frameTimer = null;
    var idleTimer = null;
    var isDragging = false;

    function docScrollMax() {
      return Math.max(
        document.documentElement.scrollHeight - window.innerHeight,
        1
      );
    }

    function currentPercent() {
      return Math.min(1, Math.max(0, window.scrollY / docScrollMax()));
    }

    function positionThumb(percent) {
      var trackRect = track.getBoundingClientRect();
      var usableWidth = trackRect.width - 40; // matches CSS 20px inset each side
      var x = 20 + usableWidth * percent;
      thumb.style.left = x + 'px';
      track.style.setProperty('--monk-progress', (percent * 100) + '%');
    }

    function setState(next) {
      if (state === next) return;
      state = next;
      frameIndex = 0;
      clearInterval(frameTimer);

      if (state === 'walking') {
        frameTimer = setInterval(function () {
          frameIndex = (frameIndex + 1) % FRAMES.walk.length;
          img.src = FRAMES.walk[frameIndex];
        }, WALK_FRAME_MS);
        img.src = FRAMES.walk[0];
      } else if (state === 'meditating') {
        frameTimer = setInterval(function () {
          frameIndex = (frameIndex + 1) % FRAMES.meditate.length;
          img.src = FRAMES.meditate[frameIndex];
        }, MEDITATE_FRAME_MS);
        img.src = FRAMES.meditate[0];
      } else {
        img.src = FRAMES.meditate[0];
      }
    }

    function onScroll() {
      positionThumb(currentPercent());
      if (!isDragging) setState('walking');
      clearTimeout(idleTimer);
      idleTimer = setTimeout(function () {
        if (!isDragging) setState('meditating');
      }, IDLE_DELAY);
    }

    // --- drag to scroll ---
    function percentFromClientX(clientX) {
      var trackRect = track.getBoundingClientRect();
      var usableWidth = trackRect.width - 40;
      var rel = (clientX - trackRect.left - 20) / usableWidth;
      return Math.min(1, Math.max(0, rel));
    }

    function scrollToPercent(percent) {
      window.scrollTo(0, percent * docScrollMax());
    }

    function startDrag(clientX) {
      isDragging = true;
      setState('walking');
      thumb.style.cursor = 'grabbing';
      scrollToPercent(percentFromClientX(clientX));
    }

    function moveDrag(clientX) {
      if (!isDragging) return;
      scrollToPercent(percentFromClientX(clientX));
    }

    function endDrag() {
      if (!isDragging) return;
      isDragging = false;
      thumb.style.cursor = 'grab';
      clearTimeout(idleTimer);
      idleTimer = setTimeout(function () { setState('meditating'); }, IDLE_DELAY);
    }

    thumb.addEventListener('mousedown', function (e) {
      e.preventDefault();
      startDrag(e.clientX);
      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    });
    function onMouseMove(e) { moveDrag(e.clientX); }
    function onMouseUp() {
      endDrag();
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    }

    thumb.addEventListener('touchstart', function (e) {
      startDrag(e.touches[0].clientX);
    }, { passive: true });
    thumb.addEventListener('touchmove', function (e) {
      moveDrag(e.touches[0].clientX);
    }, { passive: true });
    thumb.addEventListener('touchend', endDrag);

    // keyboard accessibility
    thumb.addEventListener('keydown', function (e) {
      var step = 0.02;
      var p = currentPercent();
      if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
        scrollToPercent(Math.min(1, p + step));
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
        scrollToPercent(Math.max(0, p - step));
      } else {
        return;
      }
      e.preventDefault();
    });

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', function () { positionThumb(currentPercent()); });

    // initial position
    positionThumb(currentPercent());
    setState('idle');
    setTimeout(function () { setState('meditating'); }, 300);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();