function renderChart(elementId, figure) {
  const element = document.getElementById(elementId);
  if (!element || !figure) return;
  const config = { responsive: true, displaylogo: false };
  Plotly.newPlot(element, figure.data || [], figure.layout || {}, config);
}

function setTheme(theme) {
  document.documentElement.setAttribute("data-bs-theme", theme);
  localStorage.setItem("skinseasonai-theme", theme);
  window.dispatchEvent(new Event("resize"));
}

document.addEventListener("DOMContentLoaded", () => {
  setTheme(localStorage.getItem("skinseasonai-theme") || "light");
  const toggle = document.getElementById("themeToggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-bs-theme") || "light";
      setTheme(current === "light" ? "dark" : "light");
    });
  }
});

