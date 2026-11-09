/**
 * ScholarPath AI - Ultra-Smooth Interactions & Magnetic Sliding Indicator
 */
document.addEventListener("DOMContentLoaded", function () {
  // 1. Password reveal toggle
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

  // 2. Auto-fade flash alerts after 6 seconds
  const autoAlerts = document.querySelectorAll(".alert-auto-dismiss");
  autoAlerts.forEach((alert) => {
    setTimeout(() => {
      alert.classList.add("fade");
      setTimeout(() => alert.remove(), 300);
    }, 6000);
  });

  // 3. Ultra-Smooth Sliding Magnetic Indicator for Nav Pills & Filter Tabs
  const pillContainers = document.querySelectorAll(".nav-pills");
  pillContainers.forEach((container) => {
    container.style.position = "relative";

    // Create the floating sliding highlight element
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

    // Initialize position on active tab
    if (activeItem) {
      setTimeout(() => moveTo(activeItem, true), 50);
    }

    // Hover glide effect
    items.forEach((item) => {
      item.addEventListener("mouseenter", function () {
        moveTo(this, false);
      });

      item.addEventListener("click", function () {
        activeItem = this;
        moveTo(this, false);
      });
    });

    // When mouse leaves container, smoothly glide back to active tab
    container.addEventListener("mouseleave", function () {
      if (activeItem) {
        moveTo(activeItem, false);
      }
    });

    window.addEventListener("resize", () => {
      if (activeItem) moveTo(activeItem, true);
    });
  });
});
