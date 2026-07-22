
(function () {
  const STORAGE_KEY = "ems-theme";
  const root = document.documentElement;

  function apply(theme) {
    if (theme === "light" || theme === "dark") {
      root.setAttribute("data-theme", theme);
    } else {
      root.removeAttribute("data-theme");
    }
    updateToggleUI(theme);
  }

  function currentTheme() {
    return localStorage.getItem(STORAGE_KEY) ||
      (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  }

  function updateToggleUI(theme) {
    document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
      const isDark = theme === "dark";
      btn.setAttribute("aria-pressed", isDark ? "true" : "false");
      btn.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
      btn.querySelectorAll("[data-theme-icon]").forEach((el) => {
        el.style.display = el.dataset.themeIcon === theme ? "" : "none";
      });
    });
  }

  // Initial paint (before DOMContentLoaded to avoid flash)
  const initial = currentTheme();
  apply(initial);

  document.addEventListener("DOMContentLoaded", () => {
    updateToggleUI(initial);
    document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const next = (root.getAttribute("data-theme") === "dark") ? "light" : "dark";
        localStorage.setItem(STORAGE_KEY, next);
        apply(next);
      });
    });
  });
})();
