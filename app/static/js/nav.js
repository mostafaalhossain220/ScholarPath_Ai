/**
 * ScholarPath AI — smooth in-page navigation
 *
 * Internal links (and GET filter forms) no longer do a full page reload.
 * Pages are preloaded in the background, then only the content area
 * (#sp-page) fades out and the new content glides in. The header,
 * background and petals keep running, so there is no white flash.
 *
 * - Main pages (Dashboard, Opportunities, Tracker…) are preloaded when the
 *   browser is idle; any other link is preloaded on hover / touch.
 * - Back / forward, the address bar and the tab title keep working.
 * - POST forms (save, log in, log out…) still do a normal full load, so data
 *   on screen is always fresh after a change.
 * - Anything unexpected (error page, login state changed, no #sp-page) falls
 *   back to a normal page load, so nothing can break.
 */
(function () {
  "use strict";

  if (!window.fetch || !window.DOMParser || !history.pushState) return;

  const CACHE_TTL = 60 * 1000;
  const LEAVE_MS = 170;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const cache = new Map(); // url -> { time, promise }
  const scrollPositions = new Map();
  let navToken = 0;

  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const keyOf = (url) => { const u = new URL(url, location.href); u.hash = ""; return u.href; };

  function isSwappableUrl(url) {
    let u;
    try { u = new URL(url, location.href); } catch (e) { return false; }
    if (u.origin !== location.origin) return false;
    if (!/^https?:$/.test(u.protocol)) return false;
    if (u.pathname.startsWith("/static/")) return false;
    return true;
  }

  function isSwappableLink(a) {
    if (!a || !a.href) return false;
    if (a.target && a.target !== "_self") return false;
    if (a.hasAttribute("download") || a.hasAttribute("data-no-swap")) return false;
    if (a.getAttribute("href").startsWith("#")) return false;
    // Same page, only the #hash differs: let the browser scroll
    if (keyOf(a.href) === keyOf(location.href) && new URL(a.href).hash) return false;
    return isSwappableUrl(a.href);
  }

  function fetchPage(url) {
    const key = keyOf(url);
    const hit = cache.get(key);
    if (hit && Date.now() - hit.time < CACHE_TTL) return hit.promise;

    const promise = fetch(key, { credentials: "same-origin", headers: { "X-Requested-With": "sp-nav" } })
      .then((res) => {
        const type = res.headers.get("content-type") || "";
        if (!type.includes("text/html") || res.status >= 500) throw new Error("not swappable");
        return res.text().then((html) => ({ html, url: res.url, ok: res.ok }));
      });
    cache.set(key, { time: Date.now(), promise });
    promise.catch(() => cache.delete(key));
    return promise;
  }

  function prefetch(url) {
    if (!isSwappableUrl(url)) return;
    const conn = navigator.connection;
    if (conn && (conn.saveData || /2g/.test(conn.effectiveType || ""))) return;
    fetchPage(url).catch(() => {});
  }

  function syncNav(doc) {
    // Copy the active state of header links from the new page
    document.querySelectorAll(".sp-nav-link, .account-menu .dropdown-item").forEach((link) => {
      const href = link.getAttribute("href");
      if (!href) return;
      const twin = doc.querySelector(`.sp-nav-link[href="${CSS.escape(href)}"], .account-menu .dropdown-item[href="${CSS.escape(href)}"]`);
      link.classList.toggle("active", Boolean(twin && twin.classList.contains("active")));
    });
    // Close the mobile menu and any open dropdown
    const collapse = document.getElementById("sp-nav-collapse");
    const toggle = document.getElementById("sp-nav-toggle");
    if (collapse && collapse.classList.contains("is-open")) {
      collapse.classList.remove("is-open");
      if (toggle) {
        toggle.setAttribute("aria-expanded", "false");
        const icon = toggle.querySelector("i");
        if (icon) icon.className = "bi bi-list";
      }
    }
    if (window.bootstrap) {
      document.querySelectorAll('[data-bs-toggle="dropdown"]').forEach((el) => {
        const dd = window.bootstrap.Dropdown.getInstance(el);
        if (dd) dd.hide();
      });
    }
  }

  async function go(url, opts) {
    const { push = true, restoreScroll = false } = opts || {};
    const token = ++navToken;
    const current = document.getElementById("sp-page");
    if (!current) { location.href = url; return; }

    scrollPositions.set(keyOf(location.href), window.scrollY);
    document.documentElement.classList.add("sp-navigating");
    current.classList.add("is-leaving");

    let page;
    try {
      [page] = await Promise.all([fetchPage(url), wait(reduceMotion ? 0 : LEAVE_MS)]);
    } catch (e) {
      location.href = url;
      return;
    }
    if (token !== navToken) return; // a newer click won

    const doc = new DOMParser().parseFromString(page.html, "text/html");
    const next = doc.getElementById("sp-page");
    const loggedInNow = Boolean(document.querySelector(".account-btn"));
    const loggedInNext = Boolean(doc.querySelector(".account-btn"));
    if (!next || loggedInNow !== loggedInNext) {
      // Login state or layout changed: do a real load so the header is correct
      location.href = page.url;
      return;
    }

    document.title = doc.title;
    syncNav(doc);
    current.replaceWith(document.adoptNode(next));
    if (push) history.pushState({ sp: true }, "", page.url);
    else if (page.url !== location.href) history.replaceState({ sp: true }, "", page.url);

    const y = restoreScroll ? (scrollPositions.get(keyOf(page.url)) || 0) : 0;
    window.scrollTo({ top: y, left: 0, behavior: "instant" });
    document.documentElement.classList.remove("sp-navigating");

    if (typeof window.initPage === "function") window.initPage(false);

    // Fresh data next time for the page we just showed
    cache.delete(keyOf(url));
    warmUp();
  }

  function warmUp() {
    const idle = window.requestIdleCallback || ((fn) => setTimeout(fn, 300));
    idle(() => {
      document.querySelectorAll(".sp-nav-link[href], .sp-brand[href]").forEach((a) => {
        if (isSwappableLink(a) && keyOf(a.href) !== keyOf(location.href)) prefetch(a.href);
      });
    });
  }

  function start() {
    if ("scrollRestoration" in history) history.scrollRestoration = "manual";
    history.replaceState({ sp: true }, "", location.href);

    // Links
    document.addEventListener("click", (e) => {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const a = e.target.closest("a");
      if (!isSwappableLink(a)) return;
      e.preventDefault();
      go(a.href);
    });

    // GET forms (e.g. opportunity filters) also swap smoothly
    document.addEventListener("submit", (e) => {
      const form = e.target;
      if (e.defaultPrevented || (form.method || "get").toLowerCase() !== "get") return;
      const action = form.getAttribute("action") || location.pathname;
      if (!isSwappableUrl(action)) return;
      e.preventDefault();
      const url = new URL(action, location.href);
      url.search = new URLSearchParams(new FormData(form)).toString();
      cache.delete(keyOf(url.href));
      go(url.href);
    });

    // Preload on hover (desktop) and on touch (phones)
    let hoverTimer = null;
    document.addEventListener("pointerover", (e) => {
      const a = e.target.closest && e.target.closest("a");
      if (!isSwappableLink(a)) return;
      clearTimeout(hoverTimer);
      hoverTimer = setTimeout(() => prefetch(a.href), 65);
    });
    document.addEventListener("touchstart", (e) => {
      const a = e.target.closest && e.target.closest("a");
      if (isSwappableLink(a)) prefetch(a.href);
    }, { passive: true });

    // Back / forward
    window.addEventListener("popstate", () => go(location.href, { push: false, restoreScroll: true }));

    // If a swap fell back to a full load and the user comes back via the
    // back/forward cache, never leave the old page faded out.
    window.addEventListener("pageshow", (e) => {
      if (!e.persisted) return;
      navToken++;
      document.documentElement.classList.remove("sp-navigating");
      const page = document.getElementById("sp-page");
      if (page) page.classList.remove("is-leaving");
    });

    warmUp();
  }

  window.SPNav = { start, go, prefetch };
})();
