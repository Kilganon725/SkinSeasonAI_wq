const renderedCharts = new Set();

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function themedLayout(layout = {}) {
  const textColor = cssVar("--text-main") || "#142033";
  const softColor = cssVar("--text-soft") || "#627187";
  const borderColor = cssVar("--border") || "#dde6ee";
  return {
    ...layout,
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: { ...(layout.font || {}), color: textColor },
    margin: { l: 48, r: 24, t: 58, b: 44, ...(layout.margin || {}) },
    xaxis: {
      gridcolor: borderColor,
      zerolinecolor: borderColor,
      tickfont: { color: softColor },
      ...(layout.xaxis || {}),
    },
    yaxis: {
      gridcolor: borderColor,
      zerolinecolor: borderColor,
      tickfont: { color: softColor },
      ...(layout.yaxis || {}),
    },
    legend: {
      bgcolor: "rgba(0,0,0,0)",
      ...(layout.legend || {}),
    },
    polar: {
      bgcolor: "rgba(0,0,0,0)",
      radialaxis: {
        gridcolor: borderColor,
        tickfont: { color: softColor },
        ...((layout.polar || {}).radialaxis || {}),
      },
      angularaxis: {
        gridcolor: borderColor,
        tickfont: { color: softColor },
        ...((layout.polar || {}).angularaxis || {}),
      },
      ...(layout.polar || {}),
    },
    coloraxis: {
      colorbar: {
        tickfont: { color: softColor },
        ...(((layout.coloraxis || {}).colorbar) || {}),
      },
      ...(layout.coloraxis || {}),
    },
  };
}

function renderChart(elementId, figure) {
  const element = document.getElementById(elementId);
  if (!element || !figure) return;
  const config = { responsive: true, displaylogo: false };
  Plotly.newPlot(element, figure.data || [], themedLayout(figure.layout || {}), config);
  renderedCharts.add(elementId);
}

function setTheme(theme) {
  document.documentElement.setAttribute("data-bs-theme", theme);
  localStorage.setItem("skinseasonai-theme", theme);
  renderedCharts.forEach((id) => {
    const element = document.getElementById(id);
    if (element) {
      Plotly.relayout(element, themedLayout(element.layout || {}));
    }
  });
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
