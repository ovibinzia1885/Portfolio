/* Portfolio main script ------------------------------------------------------ */
(function () {
  "use strict";

  const root = document.documentElement;
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

  /* Theme toggle (dark default, preference saved) */
  const themeBtn = $("#themeToggle");
  function applyTheme(theme) {
    root.setAttribute("data-bs-theme", theme);
    try { localStorage.setItem("theme", theme); } catch (e) { /* storage blocked */ }
    if (themeBtn) {
      themeBtn.setAttribute("aria-label", theme === "dark" ? "Switch to light theme" : "Switch to dark theme");
      $("i", themeBtn).className = theme === "dark" ? "bi bi-sun" : "bi bi-moon-stars";
    }
  }
  if (themeBtn) {
    applyTheme(root.getAttribute("data-bs-theme") || "dark");
    themeBtn.addEventListener("click", () =>
      applyTheme(root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark"));
  }

  /* Navbar: solid background after scrolling / while mobile menu is open */
  const nav = $(".navbar-portfolio");
  const collapseEl = $("#mainNav");
  function onScroll() {
    if (nav) nav.classList.toggle("scrolled", window.scrollY > 24);
    const top = $("#backToTop");
    if (top) top.classList.toggle("show", window.scrollY > 600);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  if (collapseEl && nav) {
    collapseEl.addEventListener("show.bs.collapse", () => nav.classList.add("menu-open"));
    collapseEl.addEventListener("hidden.bs.collapse", () => nav.classList.remove("menu-open"));
    $$(".nav-link", collapseEl).forEach((link) =>
      link.addEventListener("click", () => {
        if (collapseEl.classList.contains("show")) bootstrap.Collapse.getOrCreateInstance(collapseEl).hide();
      }));
  }

  /* Scroll spy for in-page links (home only) */
  const spyLinks = $$('.navbar-portfolio .nav-link[data-spy]');
  if (spyLinks.length && "IntersectionObserver" in window) {
    const map = new Map();
    spyLinks.forEach((l) => { const s = document.getElementById(l.dataset.spy); if (s) map.set(s, l); });
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          spyLinks.forEach((l) => l.classList.remove("active"));
          const l = map.get(e.target); if (l) l.classList.add("active");
        }
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    map.forEach((_, section) => spy.observe(section));
  }

  /* Reveal on scroll */
  const revealEls = $$(".reveal");
  if ("IntersectionObserver" in window && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("visible"); obs.unobserve(e.target); } });
    }, { threshold: 0.12 });
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add("visible"));
  }

  /* Project filter (buttons carry data-filter, cards carry data-tech="a,b") */
  $$("[data-filter-group]").forEach((group) => {
    const scope = group.closest("[data-filter-scope]") || document;
    const items = $$(".filter-item", scope);
    $$(".filter-btn", group).forEach((btn) => {
      btn.addEventListener("click", () => {
        $$(".filter-btn", group).forEach((b) => { b.classList.remove("active"); b.setAttribute("aria-pressed", "false"); });
        btn.classList.add("active"); btn.setAttribute("aria-pressed", "true");
        const key = btn.dataset.filter;
        items.forEach((item) => {
          const techs = (item.dataset.tech || "").split(",");
          item.classList.toggle("is-hidden", key !== "all" && !techs.includes(key));
        });
      });
    });
  });

  /* Skill tabs */
  const tabBar = $("[data-skill-tabs]");
  if (tabBar) {
    $$(".filter-btn", tabBar).forEach((btn) => btn.addEventListener("click", () => {
      $$(".filter-btn", tabBar).forEach((b) => { b.classList.remove("active"); b.setAttribute("aria-selected", "false"); });
      btn.classList.add("active"); btn.setAttribute("aria-selected", "true");
      $$(".skill-pane").forEach((p) => p.classList.toggle("active", p.id === btn.dataset.pane));
    }));
  }

  /* Messages: auto-dismiss after 7s, closable */
  $$(".toast-p").forEach((toast) => {
    const close = () => { toast.classList.add("hide"); setTimeout(() => toast.remove(), 300); };
    const btn = $(".btn-close", toast);
    if (btn) btn.addEventListener("click", close);
    setTimeout(close, 7000);
  });

  /* Contact form: client-side hints + prevent double submit */
  const form = $("[data-contact-form]");
  if (form) {
    form.addEventListener("submit", (e) => {
      if (!form.checkValidity()) {
        e.preventDefault(); e.stopPropagation();
        form.classList.add("was-validated");
        const first = $(":invalid", form); if (first) first.focus();
        return;
      }
      const btn = $("button[type=submit]", form);
      if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Sending...'; }
    });
  }

  /* Back to top */
  const topBtn = $("#backToTop");
  if (topBtn) topBtn.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

  /* Footer year */
  const year = $("#year"); if (year) year.textContent = new Date().getFullYear();
})();
