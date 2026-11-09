/**
 * ScholarPath AI - Main Interactive Utilities
 */
document.addEventListener("DOMContentLoaded", function () {
  // Toggle password visibility
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

  // Auto-fade flash alerts after 6 seconds
  const autoAlerts = document.querySelectorAll(".alert-auto-dismiss");
  autoAlerts.forEach((alert) => {
    setTimeout(() => {
      alert.classList.add("fade");
      setTimeout(() => alert.remove(), 300);
    }, 6000);
  });
});
