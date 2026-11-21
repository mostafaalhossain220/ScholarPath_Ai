/**
 * ScholarPath AI - Ultra-Smooth Interactions, Autocomplete & Flatpickr Calendar
 */
/* Runs on first load (firstRun = true) and again after every smooth page swap.
   Global, once-only behaviour is guarded by `if (firstRun)`. */
function initPage(firstRun) {
  // =========================================================================
  // 1. Password reveal toggle
  // =========================================================================
  const toggleButtons = document.querySelectorAll(".toggle-password-btn");
  toggleButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      const targetId = this.getAttribute("data-target");
      const input = document.getElementById(targetId);
      if (!input) return;
      const icon = this.querySelector("i");
      if (input.type === "password") {
        input.type = "text";
        if (icon) {
          icon.classList.remove("bi-eye");
          icon.classList.add("bi-eye-slash");
        }
      } else {
        input.type = "password";
        if (icon) {
          icon.classList.remove("bi-eye-slash");
          icon.classList.add("bi-eye");
        }
      }
    });
  });

  // =========================================================================
  // 2. Auto-fade flash alerts after 6 seconds
  // =========================================================================
  const autoAlerts = document.querySelectorAll(".alert-auto-dismiss");
  autoAlerts.forEach((alert) => {
    setTimeout(() => {
      alert.classList.add("fade");
      setTimeout(() => alert.remove(), 300);
    }, 6000);
  });

  // =========================================================================
  // 3. Ultra-Smooth Sliding Magnetic Indicator for Nav Pills & Filter Tabs
  // =========================================================================
  const pillContainers = document.querySelectorAll(".nav-pills");
  pillContainers.forEach((container) => {
    container.style.position = "relative";

    let indicator = container.querySelector(".sliding-pill-indicator");
    if (!indicator) {
      indicator = document.createElement("div");
      indicator.className = "sliding-pill-indicator";
      container.prepend(indicator);
    }

    const items = container.querySelectorAll(".nav-link");
    let activeItem = container.querySelector(".nav-link.active") || items[0];

    function moveTo(target, isInstant) {
      if (!target) return;
      const targetRect = target.getBoundingClientRect();
      const containerRect = container.getBoundingClientRect();

      const left = targetRect.left - containerRect.left;
      const top = targetRect.top - containerRect.top;
      const width = targetRect.width;
      const height = targetRect.height;

      if (isInstant) {
        indicator.style.transition = "none";
      } else {
        indicator.style.transition = "all 0.28s cubic-bezier(0.25, 1, 0.5, 1)";
      }

      indicator.style.transform = `translate3d(${left}px, ${top}px, 0)`;
      indicator.style.width = `${width}px`;
      indicator.style.height = `${height}px`;
      indicator.style.opacity = "1";
      // Only the tab under the slider gets white text
      items.forEach((el) => el.classList.toggle("is-lit", el === target));
    }

    if (activeItem) {
      container.classList.add("has-indicator");
      moveTo(activeItem, true);
      // Re-measure once fonts/layout settle
      setTimeout(() => moveTo(activeItem, true), 60);
    }

    items.forEach((item) => {
      item.addEventListener("mouseenter", function () {
        moveTo(this, false);
      });

      item.addEventListener("click", function () {
        activeItem = this;
        moveTo(this, false);
      });
    });

    container.addEventListener("mouseleave", function () {
      if (activeItem) {
        moveTo(activeItem, false);
      }
    });

    window.addEventListener("resize", () => {
      if (activeItem) moveTo(activeItem, true);
    });
  });

  // =========================================================================
  // 4. Built-in 195 World Countries with Contiguous Substring Search
  // =========================================================================
  const COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda",
    "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain",
    "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria",
    "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada",
    "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros",
    "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark",
    "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador",
    "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji",
    "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece",
    "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras",
    "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel",
    "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait",
    "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya",
    "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia",
    "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius",
    "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco",
    "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand",
    "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman",
    "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru",
    "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda",
    "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa",
    "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia",
    "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
    "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka",
    "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan",
    "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago",
    "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine",
    "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan",
    "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe",
    "UK", "USA"
  ];

  // -------------------------------------------------------------------------
  // Shared country search
  // Listing countries (from the database, e.g. "UK", "USA") come first so the
  // student picks the same spelling the opportunities use. World names that
  // mean the same place are folded into them through search aliases.
  // -------------------------------------------------------------------------
  const COUNTRY_ALIASES = {
    "UK": ["United Kingdom", "Britain", "Great Britain", "England", "Scotland", "Wales"],
    "USA": ["United States", "United States of America", "America", "US"],
    "South Korea": ["Korea"],
    "Czech Republic": ["Czechia"],
  };

  function readListing(el) {
    try { return JSON.parse(el.getAttribute("data-listing") || "[]"); } catch (e) { return []; }
  }

  function buildCountryOptions(listing) {
    const options = [];
    const seen = new Set();
    const add = (name, inListings) => {
      const key = name.toLowerCase();
      if (seen.has(key)) return;
      seen.add(key);
      const aliases = COUNTRY_ALIASES[name] || [];
      aliases.forEach((a) => seen.add(a.toLowerCase())); // hide duplicate world names
      options.push({ name, aliases, inListings });
    };
    listing.forEach((name) => add(name, true));
    COUNTRIES.forEach((name) => add(name, false));
    return options;
  }

  // Trie-style ranking: exact > prefix > word prefix > alias prefix > anywhere
  function searchCountries(options, query, limit) {
    const q = query.trim().toLowerCase();
    if (!q) return options.filter((o) => o.inListings).concat(options.filter((o) => !o.inListings)).slice(0, limit);
    const scored = [];
    options.forEach((o) => {
      const name = o.name.toLowerCase();
      let score = -1;
      if (name === q) score = 0;
      else if (name.startsWith(q)) score = 1;
      else if (name.split(/[\s-]+/).some((w) => w.startsWith(q))) score = 2;
      else if (o.aliases.some((a) => a.toLowerCase().startsWith(q))) score = 3;
      else if (name.includes(q) || o.aliases.some((a) => a.toLowerCase().includes(q))) score = 4;
      if (score >= 0) scored.push({ o, score });
    });
    scored.sort((a, b) => a.score - b.score || (b.o.inListings - a.o.inListings) || a.o.name.localeCompare(b.o.name));
    return scored.slice(0, limit).map((s) => s.o);
  }

  function escapeHtml(text) {
    return text.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function highlight(text, query) {
    const q = query.trim();
    const safe = escapeHtml(text);
    if (!q) return safe;
    const idx = text.toLowerCase().indexOf(q.toLowerCase());
    if (idx === -1) return safe;
    return escapeHtml(text.slice(0, idx)) + '<span class="match-highlight">' +
      escapeHtml(text.slice(idx, idx + q.length)) + "</span>" + escapeHtml(text.slice(idx + q.length));
  }

  function optionHtml(o, query) {
    const alias = o.aliases.find((a) => query.trim() && a.toLowerCase().includes(query.trim().toLowerCase()) &&
                                        !o.name.toLowerCase().includes(query.trim().toLowerCase()));
    return `<i class="bi bi-geo-alt-fill me-2"></i><span class="flex-grow-1">${highlight(o.name, query)}` +
      (alias ? ` <span class="opt-alias">(${escapeHtml(alias)})</span>` : "") + "</span>" +
      (o.inListings ? '<span class="opt-badge">In listings</span>' : "");
  }

  const countryInput = document.getElementById("country");
  const countryDropdown = document.getElementById("country-dropdown");

  if (countryInput && countryDropdown) {
    function highlightMatch(text, query) {
      if (!query) return text;
      const idx = text.toLowerCase().indexOf(query.toLowerCase());
      if (idx === -1) return text;
      return (
        text.substring(0, idx) +
        '<span class="match-highlight">' +
        text.substring(idx, idx + query.length) +
        "</span>" +
        text.substring(idx + query.length)
      );
    }

    const filterOptions = buildCountryOptions(readListing(countryInput));

    function renderCountries(query) {
      query = (query || "").trim();
      countryDropdown.innerHTML = "";

      const matches = searchCountries(filterOptions, query, 10);

      if (matches.length === 0) {
        countryDropdown.innerHTML = '<div class="autocomplete-item text-muted small py-2 px-3">No matching country</div>';
        countryDropdown.style.display = "block";
        return;
      }

      matches.forEach((o) => {
        const item = document.createElement("div");
        item.className = "autocomplete-item";
        item.innerHTML = optionHtml(o, query);
        item.addEventListener("click", function () {
          countryInput.value = o.name;
          countryDropdown.style.display = "none";
        });
        countryDropdown.appendChild(item);
      });

      countryDropdown.style.display = "block";
    }

    countryInput.addEventListener("input", function () {
      renderCountries(this.value);
    });

    countryInput.addEventListener("focus", function () {
      renderCountries(this.value);
    });

    document.addEventListener("click", function (e) {
      if (!countryInput.contains(e.target) && !countryDropdown.contains(e.target)) {
        countryDropdown.style.display = "none";
      }
    });
  }

  // =========================================================================
  // 4b. Multi-country chip picker (profile + AI match "Preferred countries")
  //     Search, then Enter/click to add. Stored in a hidden input as
  //     "UK, Germany, USA" so the server receives the same text as before.
  // =========================================================================
  document.querySelectorAll("[data-tag-input]").forEach((root) => {
    const hidden = root.querySelector("input[type='hidden']");
    const box = root.querySelector(".tag-input-box");
    const field = root.querySelector(".tag-input-field");
    const dropdown = root.querySelector(".autocomplete-dropdown");
    if (!hidden || !box || !field || !dropdown) return;

    const options = buildCountryOptions(readListing(root));
    const byKey = new Map();
    options.forEach((o) => {
      byKey.set(o.name.toLowerCase(), o);
      o.aliases.forEach((a) => byKey.set(a.toLowerCase(), o));
    });

    // Start from what is already saved (unknown spellings are kept but flagged)
    let tags = hidden.value.replace(/;/g, ",").split(",").map((s) => s.trim()).filter(Boolean)
      .map((raw) => {
        const match = byKey.get(raw.toLowerCase());
        return { name: match ? match.name : raw, known: Boolean(match) };
      })
      .filter((t, i, arr) => arr.findIndex((x) => x.name.toLowerCase() === t.name.toLowerCase()) === i);

    let results = [];
    let active = 0;

    function sync() {
      hidden.value = tags.map((t) => t.name).join(", ");
      box.querySelectorAll(".tag-chip").forEach((chip) => chip.remove());
      tags.forEach((t, i) => {
        const chip = document.createElement("span");
        chip.className = "tag-chip" + (t.known ? "" : " is-unknown");
        if (!t.known) chip.title = "Not in the country list. Remove it and pick from the suggestions.";
        chip.innerHTML = `${t.known ? "" : '<i class="bi bi-exclamation-triangle-fill"></i>'}<span>${escapeHtml(t.name)}</span>` +
          `<button type="button" aria-label="Remove ${escapeHtml(t.name)}"><i class="bi bi-x"></i></button>`;
        chip.querySelector("button").addEventListener("click", (e) => {
          e.stopPropagation();
          tags.splice(i, 1);
          sync();
          field.focus();
        });
        box.insertBefore(chip, field);
      });
      field.placeholder = tags.length ? "Add another…" : "Search and add countries…";
    }

    function render() {
      const chosen = new Set(tags.map((t) => t.name.toLowerCase()));
      results = searchCountries(options.filter((o) => !chosen.has(o.name.toLowerCase())), field.value, 8);
      active = Math.min(active, Math.max(results.length - 1, 0));
      dropdown.innerHTML = "";
      if (!results.length) {
        dropdown.innerHTML = '<div class="autocomplete-item text-muted small">No matching country</div>';
      }
      results.forEach((o, i) => {
        const item = document.createElement("div");
        item.className = "autocomplete-item" + (i === active ? " is-active" : "");
        item.setAttribute("role", "option");
        item.innerHTML = optionHtml(o, field.value);
        item.addEventListener("mousedown", (e) => { e.preventDefault(); add(o); });
        item.addEventListener("mouseenter", () => { active = i; highlightActive(); });
        dropdown.appendChild(item);
      });
      dropdown.style.display = "block";
    }

    function highlightActive() {
      dropdown.querySelectorAll(".autocomplete-item").forEach((el, i) => el.classList.toggle("is-active", i === active));
      const el = dropdown.children[active];
      if (el && el.scrollIntoView) el.scrollIntoView({ block: "nearest" });
    }

    function add(o) {
      if (!tags.some((t) => t.name.toLowerCase() === o.name.toLowerCase())) tags.push({ name: o.name, known: true });
      field.value = "";
      active = 0;
      sync();
      render();
    }

    field.addEventListener("focus", () => { root.classList.add("is-focused"); render(); });
    field.addEventListener("input", () => { active = 0; render(); });
    field.addEventListener("blur", () => {
      root.classList.remove("is-focused");
      setTimeout(() => { dropdown.style.display = "none"; }, 120);
    });
    field.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") { e.preventDefault(); active = Math.min(active + 1, results.length - 1); highlightActive(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); active = Math.max(active - 1, 0); highlightActive(); }
      else if (e.key === "Enter" || e.key === "," || e.key === "Tab") {
        if (field.value.trim() && results[active]) { e.preventDefault(); add(results[active]); }
        else if (e.key === "Enter") e.preventDefault(); // never submit the form by accident
      }
      else if (e.key === "Backspace" && !field.value && tags.length) { tags.pop(); sync(); render(); }
      else if (e.key === "Escape") { dropdown.style.display = "none"; }
    });
    box.addEventListener("click", () => field.focus());

    sync();
  });

  // =========================================================================
  // 5. Degree Level Contiguous Searchable Autocomplete
  // =========================================================================
  const degreeInput = document.getElementById("degree_input");
  const degreeHidden = document.getElementById("degree");
  const degreeDropdown = document.getElementById("degree-dropdown");

  if (degreeInput && degreeDropdown && degreeHidden) {
    const DEGREES = [
      { label: "Any Degree Level", value: "" },
      { label: "Master's Degree", value: "masters" },
      { label: "PhD / Doctorate", value: "phd" }
    ];

    function renderDegrees(query) {
      query = (query || "").trim().toLowerCase();
      degreeDropdown.innerHTML = "";

      const matches = DEGREES.filter(
        (d) => !query || d.label.toLowerCase().includes(query) || d.value.includes(query)
      );

      if (matches.length === 0) {
        degreeDropdown.innerHTML = '<div class="autocomplete-item text-muted small py-2 px-3">No matching degree</div>';
        degreeDropdown.style.display = "block";
        return;
      }

      matches.forEach((deg) => {
        const item = document.createElement("div");
        item.className = "autocomplete-item";
        item.innerHTML = `<i class="bi bi-mortarboard text-danger me-2"></i>${deg.label}`;
        item.addEventListener("click", function () {
          degreeInput.value = deg.label === "Any Degree Level" ? "" : deg.label;
          degreeHidden.value = deg.value;
          degreeDropdown.style.display = "none";
        });
        degreeDropdown.appendChild(item);
      });

      degreeDropdown.style.display = "block";
    }

    degreeInput.addEventListener("input", function () {
      renderDegrees(this.value);
    });

    degreeInput.addEventListener("focus", function () {
      renderDegrees(this.value);
    });

    document.addEventListener("click", function (e) {
      if (!degreeInput.contains(e.target) && !degreeDropdown.contains(e.target)) {
        degreeDropdown.style.display = "none";
      }
    });
  }

  // =========================================================================
  // 6. Aesthetic Sweet Pink Flatpickr Calendar Initialization
  // =========================================================================
  if (window.flatpickr) {
    // Clean up calendars from the previous page (smooth navigation re-runs this)
    (window.__spPickers || []).forEach((fp) => { try { fp.destroy(); } catch (e) { /* already gone */ } });
    const created = flatpickr(".flatpickr-sweet", {
      dateFormat: "Y-m-d",
      altInput: true,
      altFormat: "F j, Y",
      allowInput: true,
      animate: true,
      theme: "light",
      nextArrow: '<i class="bi bi-chevron-right text-danger"></i>',
      prevArrow: '<i class="bi bi-chevron-left text-danger"></i>',
    });
    window.__spPickers = created ? [].concat(created) : [];
  }

  // =========================================================================
  // 7. Night Mode Theme Toggle (Persisted in localStorage)
  // =========================================================================
  if (firstRun) {
  const themeToggleBtn = document.getElementById("theme-toggle-btn");
  let savedTheme = "light";
  try { savedTheme = localStorage.getItem("sp-theme") || "light"; } catch (e) { /* storage blocked */ }
  if (savedTheme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
    document.documentElement.setAttribute("data-bs-theme", "dark");
  }

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", function () {
      const isDark = document.documentElement.getAttribute("data-theme") === "dark";
      const nextTheme = isDark ? "light" : "dark";
      // Briefly enable colour transitions so the theme crossfades instead of snapping
      document.documentElement.classList.add("theme-transition");
      document.documentElement.setAttribute("data-theme", nextTheme);
      document.documentElement.setAttribute("data-bs-theme", nextTheme);
      try { localStorage.setItem("sp-theme", nextTheme); } catch (e) { /* storage blocked */ }
      setTimeout(() => document.documentElement.classList.remove("theme-transition"), 500);
    });
  }
  } // end firstRun (theme)

  // =========================================================================
  // 8. Wooden Hardboard Depth Tilt - ONLY on the 3 Dashboard Cards
  // =========================================================================
  const hardboardCards = document.querySelectorAll(".hardboard-tilt-card");
  hardboardCards.forEach((card) => {
    const MAX_TILT = 7.5;
    let rafId = null;

    function handleMove(e) {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const normX = ((x / rect.width) * 2) - 1;
      const normY = ((y / rect.height) * 2) - 1;

      // Where cursor presses down, the hardboard tilts into the screen
      const rotateX = (-normY * MAX_TILT).toFixed(2);
      const rotateY = (normX * MAX_TILT).toFixed(2);
      const shadowX = (-normX * 12).toFixed(1);
      const shadowY = (-normY * 12 + 16).toFixed(1);

      card.classList.remove("tilt-resting");
      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
      card.style.boxShadow = `${shadowX}px ${shadowY}px 28px rgba(244, 63, 94, 0.18)`;
    }

    card.addEventListener("mousemove", (e) => {
      if (rafId) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(() => handleMove(e));
    });

    card.addEventListener("mouseleave", () => {
      if (rafId) cancelAnimationFrame(rafId);
      card.classList.add("tilt-resting");
      card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
      card.style.boxShadow = "";
    });
  });

  // =========================================================================
  // 9. Auth Segmented Switcher (Smooth Switch Between Log In & Sign Up)
  // =========================================================================
  const btnShowLogin = document.getElementById("btn-show-login");
  const btnShowSignup = document.getElementById("btn-show-signup");
  const loginPanel = document.getElementById("auth-login-panel");
  const signupPanel = document.getElementById("auth-signup-panel");

  if (btnShowLogin && btnShowSignup && loginPanel && signupPanel) {
    btnShowLogin.addEventListener("click", function () {
      btnShowLogin.classList.add("active");
      btnShowSignup.classList.remove("active");
      signupPanel.style.display = "none";
      loginPanel.style.display = "block";
      loginPanel.classList.add("fade-in-quick");
      const emailInput = loginPanel.querySelector("input[type='email']");
      if (emailInput) emailInput.focus();
    });

    btnShowSignup.addEventListener("click", function () {
      btnShowSignup.classList.add("active");
      btnShowLogin.classList.remove("active");
      loginPanel.style.display = "none";
      signupPanel.style.display = "block";
      signupPanel.classList.add("fade-in-quick");
      const nameInput = signupPanel.querySelector("input[name='name']");
      if (nameInput) nameInput.focus();
    });
  }

  // =========================================================================
  // 10. Motion layer: scroll reveal, count-up numbers, navbar shadow, parallax
  // =========================================================================
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // 10a. Reveal cards as they scroll into view (staggered with --reveal-delay)
  const revealEls = document.querySelectorAll(".reveal");
  if (reduceMotion || !("IntersectionObserver" in window)) {
    revealEls.forEach((el) => el.classList.add("is-visible"));
  } else {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    revealEls.forEach((el) => revealObserver.observe(el));
  }

  // 10b. Count numbers up from 0 (dashboard stat tiles)
  document.querySelectorAll("[data-count-to]").forEach((el) => {
    const target = parseInt(el.getAttribute("data-count-to"), 10);
    if (reduceMotion || !Number.isFinite(target) || target <= 0) return;
    const duration = 900;
    const start = performance.now();
    el.textContent = "0";
    function tick(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = String(Math.round(target * eased));
      if (t < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });

  // 10c. Animate progress rings / score orbs from 0 to their value
  document.querySelectorAll(".progress-ring, .score-orb").forEach((ring) => {
    if (reduceMotion) return;
    const value = ring.style.getPropertyValue("--value");
    ring.style.setProperty("--value", "0");
    requestAnimationFrame(() => {
      requestAnimationFrame(() => ring.style.setProperty("--value", value));
    });
  });

  if (firstRun) {
  // 10d. Navbar gets a deeper shadow once the page is scrolled
  const navbar = document.querySelector(".sp-navbar");
  if (navbar) {
    const onScroll = () => navbar.classList.toggle("is-scrolled", window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // 10e. Very gentle background parallax following the mouse (desktop only)
  const bgLayer = document.querySelector(".sp-bg");
  if (bgLayer && !reduceMotion && window.matchMedia("(pointer: fine)").matches) {
    let parallaxRaf = null;
    window.addEventListener("mousemove", (e) => {
      if (parallaxRaf) return;
      parallaxRaf = requestAnimationFrame(() => {
        const x = (e.clientX / window.innerWidth - 0.5) * 2;
        const y = (e.clientY / window.innerHeight - 0.5) * 2;
        bgLayer.style.setProperty("--mx", x.toFixed(3));
        bgLayer.style.setProperty("--my", y.toFixed(3));
        parallaxRaf = null;
      });
    });
  }

  // =========================================================================
  // 11. Mobile menu (smooth height animation via CSS grid rows)
  // =========================================================================
  const navToggle = document.getElementById("sp-nav-toggle");
  const navCollapse = document.getElementById("sp-nav-collapse");
  if (navToggle && navCollapse) {
    navToggle.addEventListener("click", () => {
      const open = navCollapse.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(open));
      const icon = navToggle.querySelector("i");
      if (icon) icon.className = open ? "bi bi-x-lg" : "bi bi-list";
    });
  }
  } // end firstRun (navbar, parallax, mobile menu)

  // =========================================================================
  // 12. Toast notifications (flash messages): auto-dismiss, pause on hover
  // =========================================================================
  document.querySelectorAll(".sp-toast").forEach((toast, index) => {
    let timer = null;
    let remaining = 5500 + index * 400;
    let startedAt = 0;

    const dismiss = () => {
      if (toast.classList.contains("is-leaving")) return;
      toast.classList.add("is-leaving");
      toast.addEventListener("animationend", () => toast.remove(), { once: true });
    };
    const start = () => { startedAt = Date.now(); timer = setTimeout(dismiss, remaining); };
    const pause = () => { clearTimeout(timer); remaining -= Date.now() - startedAt; };

    toast.style.animationDelay = `${index * 90}ms`;
    toast.addEventListener("mouseenter", pause);
    toast.addEventListener("mouseleave", start);
    const closeBtn = toast.querySelector(".btn-close");
    if (closeBtn) closeBtn.addEventListener("click", dismiss);
    start();
  });

  // =========================================================================
  // 13. Button ripple + loading spinner on form submit
  // =========================================================================
  if (firstRun) document.addEventListener("pointerdown", (e) => {
    const btn = e.target.closest(".btn");
    if (!btn || reduceMotion) return;
    const rect = btn.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const ripple = document.createElement("span");
    ripple.className = "sp-ripple";
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
    ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
    btn.appendChild(ripple);
    ripple.addEventListener("animationend", () => ripple.remove(), { once: true });
  });

  // Buttons with data-loading-text show a spinner while the form submits
  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      const btn = e.submitter || form.querySelector("button[type='submit'][data-loading-text]");
      if (!btn || !btn.hasAttribute("data-loading-text")) return;
      // Defer so the submitter's value is still sent with the form
      setTimeout(() => {
        btn.dataset.originalHtml = btn.innerHTML;
        btn.classList.add("is-loading");
        btn.innerHTML = `<span class="sp-spinner" aria-hidden="true"></span>${btn.getAttribute("data-loading-text")}`;
      }, 0);
    });
  });

  // Restore buttons if the page is shown again from the back/forward cache
  if (firstRun) window.addEventListener("pageshow", (e) => {
    if (e.persisted) {
      document.querySelectorAll(".btn.is-loading").forEach((b) => {
        b.classList.remove("is-loading");
        if (b.dataset.originalHtml) b.innerHTML = b.dataset.originalHtml;
      });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initPage(true);
  if (window.SPNav) window.SPNav.start();
});
