/**
 * Monk Scroller — bottom-fixed scroll-progress bar with animated monk
 * Jekyll-compatible version
 *
 * The monk walks along a short, centered path (half the screen width).
 * He faces the direction of travel, and sits cross-legged in meditation
 * when he reaches the right end of the path (page fully read) — or when
 * the page is left still for a moment.
 *
 * Images:
 *   /assets/img/walking-monk/
 *
 * CSS:
 *   /assets/css/monk-scroller.css
 *
 * JS:
 *   /assets/js/monk-scroller.js
 */
(function () {
  'use strict';

  var config = window.MonkScrollerConfig || {};

  /*
   * Jekyll baseurl.
   *
   * In your HTML/layout, define:
   *   window.MonkScrollerConfig = {
   *     imageBase: '{{ site.baseurl }}/assets/img/walking-monk/'
   *   };
   *
   * If no configuration is supplied, "/" is used.
   */
  var IMAGE_BASE = config.imageBase || '/assets/img/walking-monk/';

  var IDLE_DELAY = config.idleDelay || 900;
  var WALK_FRAME_MS = config.walkFrameMs || 160;
  var MEDITATE_FRAME_MS = config.meditateFrameMs || 650;

  /* Fraction of the viewport width the monk's path spans, centered. */
  var PATH_FRACTION = config.pathFraction || 0.5;

  var FRAMES = {
    walk: [
      IMAGE_BASE + 'walk1.svg',
      IMAGE_BASE + 'walk2.svg',
      IMAGE_BASE + 'walk3.svg',
      IMAGE_BASE + 'walk4.svg'
    ],

    meditate: [
      IMAGE_BASE + 'meditate1.svg',
      IMAGE_BASE + 'meditate2.svg'
    ]
  };

  function init() {
    var track = document.createElement('div');
    track.id = 'monk-scroller-track';

    var thumb = document.createElement('div');
    thumb.id = 'monk-scroller-thumb';
    thumb.setAttribute('role', 'scrollbar');
    thumb.setAttribute(
      'aria-label',
      'Page scroll position — drag the monk to scroll'
    );
    thumb.tabIndex = 0;

    var hint = document.createElement('div');
    hint.className = 'monk-scroller-hint';
    hint.textContent = 'drag me';

    thumb.appendChild(hint);

    var img = document.createElement('img');
    img.alt = 'Monk used as a scroll handle: walking while reading, seated in meditation at rest';
    img.src = FRAMES.meditate[0];

    thumb.appendChild(img);
    track.appendChild(thumb);
    document.body.appendChild(track);

    var state = 'idle'; // 'idle' | 'walking' | 'meditating' | 'sitting'
    var frameIndex = 0;
    var frameTimer = null;
    var idleTimer = null;
    var isDragging = false;
    var lastScrollY = window.scrollY;
    var facing = 1; // 1 = right, -1 = left

    function docScrollMax() {
      return Math.max(
        document.documentElement.scrollHeight - window.innerHeight,
        1
      );
    }

    function currentPercent() {
      return Math.min(
        1,
        Math.max(0, window.scrollY / docScrollMax())
      );
    }

    /* Geometry of the centered walking path. */
    function pathGeometry() {
      var width = track.getBoundingClientRect().width;
      var pathWidth = width * PATH_FRACTION;
      var startX = (width - pathWidth) / 2;
      return { start: startX, width: pathWidth };
    }

    function applyFacing() {
      /* The artwork faces right; mirror it when walking left.
         The seated poses are front-facing and never flipped. */
      thumb.style.transform =
        facing === -1 ? 'translateX(-50%) scaleX(-1)' : 'translateX(-50%)';
    }

    function positionThumb(percent) {
      var geo = pathGeometry();
      var x = geo.start + geo.width * percent;

      thumb.style.left = x + 'px';

      /* Progress fill spans the same centered path (CSS: left 25%, width var). */
      track.style.setProperty(
        '--monk-progress',
        (percent * PATH_FRACTION * 100) + '%'
      );
    }

    function setState(next) {
      if (state === next) return;

      state = next;
      frameIndex = 0;

      clearInterval(frameTimer);

      if (state === 'walking') {
        applyFacing();

        frameTimer = setInterval(function () {
          frameIndex =
            (frameIndex + 1) % FRAMES.walk.length;

          img.src = FRAMES.walk[frameIndex];
        }, WALK_FRAME_MS);

        img.src = FRAMES.walk[0];

      } else if (state === 'meditating' || state === 'sitting') {
        /* Seated poses are front-facing: never mirrored. */
        thumb.style.transform = 'translateX(-50%)';

        frameTimer = setInterval(function () {
          frameIndex =
            (frameIndex + 1) % FRAMES.meditate.length;

          img.src = FRAMES.meditate[frameIndex];
        }, MEDITATE_FRAME_MS);

        img.src = FRAMES.meditate[0];

      } else {
        thumb.style.transform = 'translateX(-50%)';
        img.src = FRAMES.meditate[0];
      }
    }

    function onScroll() {
      var y = window.scrollY;

      if (y > lastScrollY) {
        facing = 1;
      } else if (y < lastScrollY) {
        facing = -1;
      }
      lastScrollY = y;

      var percent = currentPercent();
      positionThumb(percent);

      /* Update the facing even if he is already walking, so the flip
         follows the scroll direction on every event. */
      if (!isDragging && state === 'walking') {
        applyFacing();
      }

      if (!isDragging) {
        /* He sits in meditation once the page has been fully read. */
        if (percent >= 0.999) {
          setState('sitting');
        } else {
          setState('walking');
        }
      }

      clearTimeout(idleTimer);

      idleTimer = setTimeout(function () {
        if (!isDragging && state !== 'sitting') {
          setState('meditating');
        }
      }, IDLE_DELAY);
    }

    function percentFromClientX(clientX) {
      var rect = track.getBoundingClientRect();
      var geo = pathGeometry();

      var rel =
        (clientX - rect.left - geo.start) /
        geo.width;

      return Math.min(1, Math.max(0, rel));
    }

    function scrollToPercent(percent) {
      window.scrollTo(
        0,
        percent * docScrollMax()
      );
    }

    function startDrag(clientX) {
      isDragging = true;
      setState('walking');

      thumb.style.cursor = 'grabbing';

      scrollToPercent(
        percentFromClientX(clientX)
      );
    }

    function moveDrag(clientX) {
      if (!isDragging) return;

      scrollToPercent(
        percentFromClientX(clientX)
      );
    }

    function endDrag() {
      if (!isDragging) return;

      isDragging = false;
      thumb.style.cursor = 'grab';

      if (currentPercent() >= 0.999) {
        setState('sitting');
        return;
      }

      clearTimeout(idleTimer);

      idleTimer = setTimeout(function () {
        setState('meditating');
      }, IDLE_DELAY);
    }

    // Mouse dragging
    thumb.addEventListener('mousedown', function (e) {
      e.preventDefault();

      startDrag(e.clientX);

      window.addEventListener(
        'mousemove',
        onMouseMove
      );

      window.addEventListener(
        'mouseup',
        onMouseUp
      );
    });

    function onMouseMove(e) {
      moveDrag(e.clientX);
    }

    function onMouseUp() {
      endDrag();

      window.removeEventListener(
        'mousemove',
        onMouseMove
      );

      window.removeEventListener(
        'mouseup',
        onMouseUp
      );
    }

    // Touch dragging
    thumb.addEventListener(
      'touchstart',
      function (e) {
        startDrag(e.touches[0].clientX);
      },
      { passive: true }
    );

    thumb.addEventListener(
      'touchmove',
      function (e) {
        moveDrag(e.touches[0].clientX);
      },
      { passive: true }
    );

    thumb.addEventListener(
      'touchend',
      endDrag
    );

    // Keyboard accessibility
    thumb.addEventListener(
      'keydown',
      function (e) {
        var step = 0.02;
        var p = currentPercent();

        if (
          e.key === 'ArrowRight' ||
          e.key === 'ArrowUp'
        ) {
          scrollToPercent(
            Math.min(1, p + step)
          );

        } else if (
          e.key === 'ArrowLeft' ||
          e.key === 'ArrowDown'
        ) {
          scrollToPercent(
            Math.max(0, p - step)
          );

        } else {
          return;
        }

        e.preventDefault();
      }
    );

    window.addEventListener(
      'scroll',
      onScroll,
      { passive: true }
    );

    window.addEventListener(
      'resize',
      function () {
        positionThumb(currentPercent());
      }
    );

    // Initial position
    positionThumb(currentPercent());

    setState('idle');

    setTimeout(function () {
      if (currentPercent() >= 0.999) {
        setState('sitting');
      } else {
        setState('meditating');
      }
    }, 300);
  }

  if (document.readyState === 'loading') {
    document.addEventListener(
      'DOMContentLoaded',
      init
    );
  } else {
    init();
  }

})();
