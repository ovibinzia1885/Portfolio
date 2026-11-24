/* Portfolio main script ------------------------------------------------------ */
(function () {
  "use strict";

  const root = document.documentElement;
  const $ = (sel, ctx = document) => ctx.querySelector(sel);
  const $$ = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

  /* Theme toggle (dark default, preference saved). There is one button in the
     sidebar, one in the mobile menu and one in the top bar. */
  const themeBtns = $$(".theme-toggle");
  function applyTheme(theme) {
    root.setAttribute("data-bs-theme", theme);
    try { localStorage.setItem("theme", theme); } catch (e) { /* storage blocked */ }
    themeBtns.forEach((btn) => {
      btn.setAttribute("aria-label", theme === "dark" ? "Switch to light theme" : "Switch to dark theme");
      const icon = $("i", btn); if (icon) icon.className = theme === "dark" ? "bi bi-sun" : "bi bi-moon-stars";
    });
  }
  applyTheme(root.getAttribute("data-bs-theme") || "dark");
  themeBtns.forEach((btn) => btn.addEventListener("click", () =>
    applyTheme(root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark")));

  /* Mobile menu: close the off-canvas after choosing a link */
  const offcanvasEl = $("#mobileNav");
  if (offcanvasEl && window.bootstrap) {
    $$(".snav-link", offcanvasEl).forEach((link) => link.addEventListener("click", () =>
      bootstrap.Offcanvas.getOrCreateInstance(offcanvasEl).hide()));
  }

  /* Back-to-top visibility */
  const topBtn = $("#backToTop");
  function onScroll() { if (topBtn) topBtn.classList.toggle("show", window.scrollY > 600); }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  if (topBtn) topBtn.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

  /* Scroll spy for in-page links (only sections that exist on this page) */
  const spyLinks = $$(".snav-link[data-spy]");
  if (spyLinks.length && "IntersectionObserver" in window) {
    const sections = new Map();
    spyLinks.forEach((link) => {
      const section = document.getElementById(link.dataset.spy);
      if (!section) return;
      if (!sections.has(section)) sections.set(section, []);
      sections.get(section).push(link);
    });
    if (sections.size) {
      const spy = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          spyLinks.forEach((l) => l.classList.remove("active"));
          (sections.get(entry.target) || []).forEach((l) => l.classList.add("active"));
        });
      }, { rootMargin: "-40% 0px -55% 0px" });
      sections.forEach((_, section) => spy.observe(section));
    }
  }

  /* Reveal on scroll */
  const revealEls = $$(".reveal");
  if ("IntersectionObserver" in window && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("visible"); obs.unobserve(e.target); } });
    }, { threshold: 0.1 });
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

  /* Certificate preview modal (image or PDF) */
  const certModal = $("#certPreview");
  if (certModal) {
    const body = $("[data-cert-body]", certModal);
    certModal.addEventListener("show.bs.modal", (event) => {
      const trigger = event.relatedTarget;
      if (!trigger) return;
      const src = trigger.dataset.certSrc;
      const title = trigger.dataset.certTitle || "Certificate";
      $("#certPreviewTitle", certModal).textContent = title;
      $("[data-cert-open]", certModal).href = src;
      $("[data-cert-download]", certModal).href = src;
      body.replaceChildren();
      if (trigger.dataset.certType === "pdf") {
        const frame = document.createElement("iframe");
        frame.src = src; frame.title = title;
        body.appendChild(frame);
      } else {
        const img = document.createElement("img");
        img.src = src; img.alt = title;
        body.appendChild(img);
      }
    });
    certModal.addEventListener("hidden.bs.modal", () => body.replaceChildren());
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

  /* Footer year */
  const year = $("#year"); if (year) year.textContent = new Date().getFullYear();
})();
