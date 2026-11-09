/**
 * ScholarPath AI - Ultra-Smooth Interactions, Autocomplete & Flatpickr Calendar
 */
document.addEventListener("DOMContentLoaded", function () {
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
    }

    if (activeItem) {
      setTimeout(() => moveTo(activeItem, true), 50);
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

    function renderCountries(query) {
      query = (query || "").trim();
      countryDropdown.innerHTML = "";

      let matches = [];
      if (!query) {
        matches = ["United Kingdom", "United States", "Germany", "Canada", "Australia", "Sweden", "Japan", "South Korea"];
      } else {
        matches = COUNTRIES.filter((c) => c.toLowerCase().includes(query.toLowerCase())).slice(0, 10);
      }

      if (matches.length === 0) {
        countryDropdown.innerHTML = '<div class="autocomplete-item text-muted small py-2 px-3">No matching country</div>';
        countryDropdown.style.display = "block";
        return;
      }

      matches.forEach((country) => {
        const item = document.createElement("div");
        item.className = "autocomplete-item";
        item.innerHTML = `<i class="bi bi-geo-alt-fill text-danger me-2"></i>${highlightMatch(country, query)}`;
        item.addEventListener("click", function () {
          countryInput.value = country;
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
    flatpickr(".flatpickr-sweet", {
      dateFormat: "Y-m-d",
      altInput: true,
      altFormat: "F j, Y",
      allowInput: true,
      animate: true,
      theme: "light",
      nextArrow: '<i class="bi bi-chevron-right text-danger"></i>',
      prevArrow: '<i class="bi bi-chevron-left text-danger"></i>',
    });
  }

  // =========================================================================
  // 7. Interactive 3D Hardboard Depth Tilt ("Hardbord e jata deoa" Physics)
  // =========================================================================
  const tiltCards = document.querySelectorAll(".tilt-press-card, .card:not(.table-card)");

  tiltCards.forEach((card) => {
    card.classList.add("tilt-press-card");

    // Add specular gloss sheen layer if not present
    let sheen = card.querySelector(".card-sheen");
    if (!sheen) {
      sheen = document.createElement("div");
      sheen.className = "card-sheen";
      card.appendChild(sheen);
    }

    const MAX_TILT = 8; // degrees of tilt
    let rafId = null;

    function handleMove(e) {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Normalized coordinates from -1 (top/left) to +1 (bottom/right)
      const normX = ((x / rect.width) * 2) - 1;
      const normY = ((y / rect.height) * 2) - 1;

      // "Hardbord e jata deoa": The side where cursor presses down tilts into the screen
      // Top pressed (normY < 0) -> rotateX positive
      // Bottom pressed (normY > 0) -> rotateX negative
      // Left pressed (normX < 0) -> rotateY negative
      // Right pressed (normX > 0) -> rotateY positive
      const rotateX = (-normY * MAX_TILT).toFixed(2);
      const rotateY = (normX * MAX_TILT).toFixed(2);

      // Dynamic reactive shadow movement opposite to the tilt pressure
      const shadowX = (-normX * 14).toFixed(1);
      const shadowY = (-normY * 14 + 18).toFixed(1);

      card.classList.remove("tilt-resting");
      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.018, 1.018, 1.018)`;
      card.style.boxShadow = `${shadowX}px ${shadowY}px 32px rgba(244, 63, 94, 0.18)`;

      if (sheen) {
        sheen.style.background = `radial-gradient(circle 280px at ${x}px ${y}px, rgba(255, 255, 255, 0.45) 0%, rgba(255, 255, 255, 0) 70%)`;
      }
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
      if (sheen) {
        sheen.style.background = "";
      }
    });
  });
});
