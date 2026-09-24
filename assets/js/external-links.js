/*
 * Open external links in a new tab; keep internal links in the same tab.
 *
 * Runs on every page (included via _includes/head.html and injected into the
 * static quiz/Pāḷi pages). A link is "external" when its resolved host
 * differs from the host of the current page.
 *
 * Skipped on purpose:
 *   - links without href, pure #fragments
 *   - mailto:, tel:, javascript:, data:
 * Internal links never open a new tab: a hardcoded target="_blank" (e.g. the
 * footer's RSS icon) is removed.
 */
(function () {
  'use strict';

  function isExternal(href) {
    if (!href) return false;
    var trimmed = href.trim();
    if (trimmed === '' || trimmed.charAt(0) === '#') return false;
    if (/^(mailto|tel|javascript|data):/i.test(trimmed)) return false;
    try {
      var url = new URL(trimmed, window.location.href);
      return url.host !== '' && url.host !== window.location.host;
    } catch (e) {
      return false;
    }
  }

  function process() {
    var links = document.querySelectorAll('a[href]');
    for (var i = 0; i < links.length; i++) {
      var a = links[i];
      if (!isExternal(a.getAttribute('href'))) {
        // internal: same tab, even if a target was hardcoded in the HTML
        if (a.hasAttribute('target')) a.removeAttribute('target');
        continue;
      }
      if (!a.hasAttribute('target')) a.setAttribute('target', '_blank');
      // keep any existing rel (e.g. nofollow) and add the security ones
      var rel = a.getAttribute('rel') || '';
      if (!/(^|\s)noopener(\s|$)/.test(rel)) rel += (rel ? ' ' : '') + 'noopener';
      if (!/(^|\s)noreferrer(\s|$)/.test(rel)) rel += ' noreferrer';
      a.setAttribute('rel', rel.trim());
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', process);
  } else {
    process();
  }
})();
