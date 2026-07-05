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

function initAuthPage() {
  const tabsRoot = document.querySelector(".auth-tabs");
  if (!tabsRoot) return;

  const setActiveTab = (mode) => {
    const nextMode = mode === "register" ? "register" : "login";
    tabsRoot.dataset.active = nextMode;
    tabsRoot.querySelectorAll(".auth-tab").forEach((tab) => {
      const isActive = tab.dataset.authTab === nextMode;
      tab.classList.toggle("active", isActive);
      tab.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    document.querySelectorAll("[data-auth-panel]").forEach((panel) => {
      panel.classList.toggle("active", panel.dataset.authPanel === nextMode);
    });
  };

  document.querySelectorAll("[data-auth-tab]").forEach((trigger) => {
    trigger.addEventListener("click", () => setActiveTab(trigger.dataset.authTab));
  });

  document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const input = button.closest(".auth-input-wrap")?.querySelector(".auth-password-input");
      if (!input) return;
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      button.innerHTML = show ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
      button.setAttribute("aria-label", show ? "隐藏密码" : "显示密码");
    });
  });

  const initialMode = tabsRoot.querySelector(".auth-tab.active")?.dataset.authTab || "login";
  setActiveTab(initialMode);
}

document.addEventListener("DOMContentLoaded", () => {
  setTheme(localStorage.getItem("skinseasonai-theme") || "light");
  initAuthPage();
  const toggle = document.getElementById("themeToggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-bs-theme") || "light";
      setTheme(current === "light" ? "dark" : "light");
    });
  }
});

