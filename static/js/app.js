(function () {
  // -------- Sidebar (mobile) --------
  const menuBtn = document.querySelector("[data-menu-toggle]");
  const sidebar = document.querySelector("[data-sidebar]");
  const scrim   = document.querySelector("[data-sidebar-scrim]");

  function openSidebar() { sidebar?.classList.add("is-open"); scrim?.classList.add("is-open"); }
  function closeSidebar() { sidebar?.classList.remove("is-open"); scrim?.classList.remove("is-open"); }
  menuBtn?.addEventListener("click", openSidebar);
  scrim?.addEventListener("click", closeSidebar);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeSidebar(); });

  // -------- Auto-dismiss flash toasts --------
  document.querySelectorAll(".toast").forEach((t) => {
    const timeout = parseInt(t.dataset.timeout || "4000", 10);
    if (timeout > 0) setTimeout(() => dismissToast(t), timeout);
    t.querySelector(".toast__close")?.addEventListener("click", () => dismissToast(t));
  });
  function dismissToast(t) {
    t.style.transition = "opacity .2s, transform .2s";
    t.style.opacity = "0";
    t.style.transform = "translateX(20px)";
    setTimeout(() => t.remove(), 200);
  }

  // -------- Table row selection --------
  const checkAll = document.querySelector("[data-check-all]");
  const rowChecks = document.querySelectorAll("[data-check-row]");
  const selBar   = document.querySelector("[data-selection-bar]");
  const selCount = document.querySelector("[data-selection-count]");

  function refreshSelection() {
    if (!selBar) return;
    const checked = document.querySelectorAll("[data-check-row]:checked").length;
    if (checked > 0) {
      selBar.classList.add("is-visible");
      if (selCount) selCount.textContent = checked;
    } else {
      selBar.classList.remove("is-visible");
    }
    if (checkAll && rowChecks.length) {
      checkAll.checked = checked === rowChecks.length;
      checkAll.indeterminate = checked > 0 && checked < rowChecks.length;
    }
  }
  checkAll?.addEventListener("change", () => {
    rowChecks.forEach((c) => { c.checked = checkAll.checked; });
    refreshSelection();
  });
  rowChecks.forEach((c) => c.addEventListener("change", refreshSelection));
  document.querySelector("[data-clear-selection]")?.addEventListener("click", () => {
    rowChecks.forEach((c) => (c.checked = false));
    if (checkAll) checkAll.checked = false;
    refreshSelection();
  });

  // -------- Delete confirm modal --------
  const modal = document.querySelector("[data-confirm-modal]");
  const modalMessage = modal?.querySelector("[data-confirm-message]");
  const modalConfirm = modal?.querySelector("[data-confirm-ok]");
  const modalCancel  = modal?.querySelector("[data-confirm-cancel]");
  let pendingHref = null;

  document.querySelectorAll("[data-confirm-delete]").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      pendingHref = el.getAttribute("href") || el.dataset.href;
      const name = el.dataset.confirmName;
      if (modalMessage && name) {
        modalMessage.innerHTML = `You are about to permanently delete <strong>${name}</strong>. This action cannot be undone.`;
      }
      modal?.classList.add("is-open");
    });
  });
  modalCancel?.addEventListener("click", () => modal?.classList.remove("is-open"));
  modal?.addEventListener("click", (e) => { if (e.target === modal) modal.classList.remove("is-open"); });
  modalConfirm?.addEventListener("click", () => {
    if (pendingHref) window.location.href = pendingHref;
  });

  // -------- Search debounce (auto-submit) --------
  const debouncedForm = document.querySelector("[data-search-debounce]");
  if (debouncedForm) {
    const input = debouncedForm.querySelector("input[name='search']");
    let t;
    input?.addEventListener("input", () => {
      clearTimeout(t);
      t = setTimeout(() => debouncedForm.submit(), 450);
    });
  }

  // -------- Global "/" search shortcut --------
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && document.activeElement?.tagName !== "INPUT" && document.activeElement?.tagName !== "TEXTAREA") {
      const search = document.querySelector("[data-global-search]");
      if (search) { e.preventDefault(); search.focus(); }
    }
  });

  // -------- Form: character progress for phone --------
  document.querySelectorAll("[data-phone-input]").forEach((inp) => {
    inp.addEventListener("input", () => {
      inp.value = inp.value.replace(/\D/g, "").slice(0, 10);
    });
  });

  // -------- Client-side inline validation hints --------
  document.querySelectorAll("form[data-validate]").forEach((f) => {
    f.addEventListener("submit", (e) => {
      let ok = true;
      f.querySelectorAll("[data-required]").forEach((el) => {
        const err = el.parentElement.querySelector(".field__error");
        if (!el.value?.trim()) {
          ok = false;
          el.classList.add("has-error");
          if (err) err.style.display = "flex";
        } else {
          el.classList.remove("has-error");
          if (err) err.style.display = "none";
        }
      });
      if (!ok) {
        e.preventDefault();
        f.querySelector(".has-error")?.focus();
      }
    });
  });
})();
