
(function () {
  if (typeof window.Chart === "undefined") return;

  const root = getComputedStyle(document.documentElement);
  const isDark = () => document.documentElement.getAttribute("data-theme") === "dark";

  const palette = [
    "#6366f1", "#06b6d4", "#10b981", "#f59e0b",
    "#ec4899", "#8b5cf6", "#14b8a6", "#f97316",
    "#3b82f6", "#eab308"
  ];

  function textColor() { return isDark() ? "#c0c6d4" : "#475569"; }
  function gridColor() { return isDark() ? "rgba(255,255,255,0.06)" : "rgba(15,23,42,0.06)"; }

  Chart.defaults.font.family = '"Plus Jakarta Sans","Segoe UI",sans-serif';
  Chart.defaults.font.size = 12;
  Chart.defaults.color = textColor();
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.boxWidth = 8;
  Chart.defaults.plugins.legend.labels.padding = 14;
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 8;
  Chart.defaults.plugins.tooltip.backgroundColor = isDark() ? "#1a1c27" : "#0f172a";
  Chart.defaults.plugins.tooltip.titleColor = "#fff";
  Chart.defaults.plugins.tooltip.bodyColor = "#e2e8f0";
  Chart.defaults.plugins.tooltip.borderColor = "rgba(255,255,255,0.08)";
  Chart.defaults.plugins.tooltip.borderWidth = 1;

  window.EMSCharts = {
    palette,
    bar(canvasId, labels, values, label) {
      const el = document.getElementById(canvasId);
      if (!el) return;
      const ctx = el.getContext("2d");
      const gradient = ctx.createLinearGradient(0, 0, 0, 300);
      gradient.addColorStop(0, "rgba(99,102,241,0.9)");
      gradient.addColorStop(1, "rgba(99,102,241,0.35)");
      return new Chart(el, {
        type: "bar",
        data: {
          labels,
          datasets: [{
            label: label || "Employees",
            data: values,
            backgroundColor: gradient,
            borderRadius: 8,
            borderSkipped: false,
            maxBarThickness: 42,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, grid: { color: gridColor() }, ticks: { precision: 0 } },
            x: { grid: { display: false } }
          }
        }
      });
    },
    doughnut(canvasId, labels, values) {
      const el = document.getElementById(canvasId);
      if (!el) return;
      return new Chart(el, {
        type: "doughnut",
        data: {
          labels,
          datasets: [{
            data: values,
            backgroundColor: palette,
            borderColor: isDark() ? "#14161f" : "#ffffff",
            borderWidth: 3,
            hoverOffset: 8,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "68%",
          plugins: {
            legend: { position: "bottom", labels: { padding: 12 } }
          }
        }
      });
    }
  };
})();