/* ==========================================================================
   Aurum & Ivy — storefront behaviour
   Progressive enhancement only: every form works without JavaScript.
   ========================================================================== */
(function () {
  "use strict";

  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));
  const csrf = ($('meta[name="csrf-token"]') || {}).content || "";

  /* ----------------------------------------------------------------- utils */
  function debounce(fn, wait = 120) {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), wait);
    };
  }

  function toast(message, kind = "success") {
    if (!message) return;
    let stack = $("[data-toasts]");
    if (!stack) {
      stack = document.createElement("div");
      stack.className = "toast-stack";
      stack.setAttribute("data-toasts", "");
      document.body.appendChild(stack);
    }
    const node = document.createElement("div");
    node.className = `toast toast-${kind}`;
    node.setAttribute("role", "status");

    const text = document.createElement("span");
    text.textContent = message;
    const close = document.createElement("button");
    close.type = "button";
    close.className = "toast-close";
    close.setAttribute("aria-label", "Dismiss");
    close.textContent = "\u00d7";
    close.addEventListener("click", () => dismiss(node));

    node.append(text, close);
    stack.appendChild(node);
    setTimeout(() => dismiss(node), 5000);
  }

  function dismiss(node) {
    if (!node || !node.parentNode) return;
    node.classList.add("is-leaving");
    setTimeout(() => node.remove(), 320);
  }

  $$(".toast").forEach((node) => {
    const close = $(".toast-close", node);
    if (close) close.addEventListener("click", () => dismiss(node));
    setTimeout(() => dismiss(node), 6000);
  });

  async function post(url, body) {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRF-Token": csrf,
        "X-Requested-With": "XMLHttpRequest",
        Accept: "application/json",
      },
      body,
      credentials: "same-origin",
    });
    let data = {};
    try {
      data = await response.json();
    } catch (error) {
      data = {};
    }
    return { ok: response.ok, status: response.status, data };
  }

  /* ---------------------------------------------------------------- header */
  const header = $("[data-header]");
  if (header) {
    const onScroll = () => header.classList.toggle("is-scrolled", window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  const searchToggle = $("[data-search-toggle]");
  const searchPanel = $("#search-panel");
  if (searchToggle && searchPanel) {
    searchToggle.addEventListener("click", () => {
      const open = searchPanel.hasAttribute("hidden");
      searchPanel.toggleAttribute("hidden", !open);
      searchToggle.setAttribute("aria-expanded", String(open));
      if (open) {
        const input = $("[data-search-input]", searchPanel);
        if (input) input.focus();
      }
    });
  }

  const navToggle = $("[data-nav-toggle]");
  const mobileNav = $("#mobile-nav");
  if (navToggle && mobileNav) {
    navToggle.addEventListener("click", () => {
      const open = mobileNav.hasAttribute("hidden");
      mobileNav.toggleAttribute("hidden", !open);
      navToggle.setAttribute("aria-expanded", String(open));
      document.body.classList.toggle("nav-open", open);
    });
  }

  const drop = $(".nav-drop");
  if (drop) {
    const button = $(".nav-drop-btn", drop);
    if (button) {
      button.addEventListener("click", (event) => {
        event.preventDefault();
        const open = drop.classList.toggle("is-open");
        button.setAttribute("aria-expanded", String(open));
      });
      document.addEventListener("click", (event) => {
        if (!drop.contains(event.target)) {
          drop.classList.remove("is-open");
          button.setAttribute("aria-expanded", "false");
        }
      });
      drop.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
          drop.classList.remove("is-open");
          button.setAttribute("aria-expanded", "false");
          button.focus();
        }
      });
    }
  }

  /* ----------------------------------------------------------- cart drawer */
  const drawer = $("#cart-drawer");
  const scrim = $("[data-scrim]");
  const drawerList = $("[data-drawer-list]");
  const drawerEmpty = $("[data-drawer-empty]");
  let lastFocus = null;

  function openDrawer() {
    if (!drawer) return;
    lastFocus = document.activeElement;
    drawer.classList.add("is-open");
    drawer.setAttribute("aria-hidden", "false");
    if (scrim) {
      scrim.removeAttribute("hidden");
      requestAnimationFrame(() => scrim.classList.add("is-open"));
    }
    document.body.style.overflow = "hidden";
    const close = $("[data-cart-close]", drawer);
    if (close) close.focus();
  }

  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove("is-open");
    drawer.setAttribute("aria-hidden", "true");
    if (scrim) {
      scrim.classList.remove("is-open");
      setTimeout(() => scrim.setAttribute("hidden", ""), 350);
    }
    document.body.style.overflow = "";
    if (lastFocus && typeof lastFocus.focus === "function") lastFocus.focus();
  }

  $$("[data-cart-open]").forEach((button) => {
    button.addEventListener("click", async () => {
      await refreshDrawer();
      openDrawer();
    });
  });
  $$("[data-cart-close]").forEach((button) => button.addEventListener("click", closeDrawer));
  if (scrim) scrim.addEventListener("click", closeDrawer);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && drawer && drawer.classList.contains("is-open")) closeDrawer();
  });

  function setBadge(count) {
    $$("[data-cart-count]").forEach((node) => {
      node.textContent = count;
      node.hidden = !count;
    });
    const drawerCount = $("[data-drawer-count]");
    if (drawerCount) drawerCount.textContent = `(${count})`;
  }

  function drawerRow(item) {
    const li = document.createElement("li");
    li.className = "drawer-item";

    const thumb = document.createElement("a");
    thumb.className = "drawer-thumb";
    thumb.href = `/product/${item.slug}`;
    const img = document.createElement("img");
    img.src = item.image;
    img.alt = item.name;
    img.loading = "lazy";
    thumb.appendChild(img);

    const body = document.createElement("div");
    body.className = "drawer-item-body";
    const name = document.createElement("a");
    name.className = "drawer-item-name";
    name.href = `/product/${item.slug}`;
    name.textContent = item.name;
    const variant = document.createElement("span");
    variant.className = "drawer-item-variant";
    variant.textContent = item.variant || "";

    const actions = document.createElement("div");
    actions.className = "drawer-item-actions";
    const qty = document.createElement("div");
    qty.className = "drawer-qty";
    const minus = quantityButton("\u2212", item, item.quantity - 1, "Decrease quantity");
    const value = document.createElement("span");
    value.textContent = item.quantity;
    const plus = quantityButton("+", item, item.quantity + 1, "Increase quantity");
    qty.append(minus, value, plus);

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "drawer-remove";
    remove.textContent = "Remove";
    remove.addEventListener("click", () => updateLine(item.key, 0));

    actions.append(qty, remove);
    body.append(name, variant, actions);

    const price = document.createElement("span");
    price.className = "drawer-item-price";
    price.textContent = item.line_display;

    li.append(thumb, body, price);
    return li;
  }

  function quantityButton(label, item, quantity, aria) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.setAttribute("aria-label", aria);
    button.addEventListener("click", () => updateLine(item.key, quantity));
    return button;
  }

  async function updateLine(key, quantity) {
    const { ok, data } = await post("/cart/update", new URLSearchParams({ key, quantity: String(quantity) }));
    if (ok) {
      renderDrawer(data);
      if (document.querySelector(".cart-lines")) window.location.reload();
    } else {
      toast((data && data.error) || "Could not update your bag.", "error");
    }
  }

  function renderDrawer(payload) {
    if (!payload) return;
    setBadge(payload.count || 0);
    const subtotal = $("[data-drawer-subtotal]");
    if (subtotal) subtotal.textContent = payload.subtotal_display || "\u20b90";
    if (drawerList) {
      drawerList.innerHTML = "";
      (payload.items || []).forEach((item) => drawerList.appendChild(drawerRow(item)));
    }
    if (drawerEmpty) drawerEmpty.hidden = Boolean(payload.count);
  }

  async function refreshDrawer() {
    try {
      const response = await fetch("/api/cart", {
        headers: { Accept: "application/json", "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin",
      });
      if (response.ok) renderDrawer(await response.json());
    } catch (error) {
      /* offline — the bag page still works */
    }
  }

  /* -------------------------------------------------------- ajax form posts */
  $$("[data-cart-form]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const submitter = event.submitter || null;
      const formData = submitter ? new FormData(form, submitter) : new FormData(form);
      const { ok, data } = await post(form.action, new URLSearchParams(formData));
      if (!ok) {
        toast((data && data.error) || "That did not work. Please try again.", "error");
        return;
      }
      renderDrawer(data);
      if (form.classList.contains("card-quick") || form.classList.contains("buy-form")) {
        toast(data.message || "Added to your bag.");
        openDrawer();
      } else {
        window.location.reload();
      }
    });
  });

  $$("[data-wishlist-form]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const { ok, data } = await post(form.action, new URLSearchParams(new FormData(form)));
      if (!ok) {
        if (data && data.error) toast(data.error, "error");
        else window.location.href = "/login";
        return;
      }
      $$("button", form).forEach((button) => {
        button.classList.toggle("is-saved", Boolean(data.saved));
        button.setAttribute("aria-pressed", String(Boolean(data.saved)));
      });
      const label = $("[data-wishlist-btn] span", form);
      if (label) label.textContent = data.saved ? "Saved to wishlist" : "Save for later";
      toast(data.message || "Wishlist updated.");
    });
  });

  $$("[data-autosubmit-select]").forEach((select) => {
    select.addEventListener("change", () => {
      const form = select.closest("form");
      if (form) form.submit();
    });
  });

  /* ------------------------------------------------------------- quantity */
  $$("[data-stepper]").forEach((stepper) => {
    const input = $("input", stepper);
    if (!input) return;
    $$("[data-step]", stepper).forEach((button) => {
      button.addEventListener("click", () => {
        const min = parseInt(input.min || "1", 10);
        const max = parseInt(input.max || "99", 10);
        const next = (parseInt(input.value || "1", 10) || 1) + parseInt(button.dataset.step, 10);
        input.value = Math.min(Math.max(next, min), max);
        input.dispatchEvent(new Event("change", { bubbles: true }));
      });
    });
  });

  $$("[data-variant-input]").forEach((input) => {
    input.addEventListener("change", () => {
      const label = $("[data-variant-label]");
      if (label && input.checked) label.textContent = input.value;
    });
  });

  /* --------------------------------------------------------------- filters */
  const filtersToggle = $("[data-filters-toggle]");
  const filters = $("[data-filters]");
  if (filtersToggle && filters) {
    filtersToggle.addEventListener("click", () => {
      const open = filters.classList.toggle("is-open");
      filtersToggle.setAttribute("aria-expanded", String(open));
    });
  }

  $$("[data-fill-promo]").forEach((button) => {
    button.addEventListener("click", () => {
      const input = $("#promo_code");
      if (input) {
        input.value = button.dataset.fillPromo;
        input.focus();
      }
    });
  });

  /* -------------------------------------------------------------- checkout */
  const paymentRadios = $$("[data-payment-radio]");
  if (paymentRadios.length) {
    const syncPanels = () => {
      const selected = paymentRadios.find((radio) => radio.checked);
      const value = selected ? selected.value : "";
      $$("[data-payment-panel]").forEach((panel) => {
        panel.hidden = panel.dataset.paymentPanel !== value;
      });
    };
    paymentRadios.forEach((radio) => radio.addEventListener("change", syncPanels));
    syncPanels();
  }

  const summary = $("[data-summary]");
  const deliveryRadios = $$("[data-delivery-radio]");
  if (summary && deliveryRadios.length) {
    const standard = Number(summary.dataset.shippingStandard || 0);
    const express = Number(summary.dataset.shippingExpress || 0);
    const baseShipping = Number(summary.dataset.shippingCurrent || 0);
    const baseTotal = Number(summary.dataset.total || 0);
    const shippingLine = $("[data-shipping-line]", summary);
    const totalLine = $("[data-total-line]", summary);

    const money = (value) =>
      "\u20b9" + String(Math.round(value)).replace(/\B(?=(\d{3})+(?!\d))/g, ",");

    const syncTotals = () => {
      const selected = deliveryRadios.find((radio) => radio.checked);
      const shipping = selected && selected.value === "express" ? express : standard;
      if (shippingLine) {
        shippingLine.textContent = shipping ? money(shipping) : "Complimentary";
        shippingLine.classList.toggle("is-free", shipping === 0);
      }
      if (totalLine) totalLine.textContent = money(baseTotal - baseShipping + shipping);
      summary.dataset.shippingCurrent = String(shipping);
    };
    deliveryRadios.forEach((radio) => radio.addEventListener("change", syncTotals));
    syncTotals();
  }

  /* ------------------------------------------------------------- mobile nav */
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    if (mobileNav && !mobileNav.hasAttribute("hidden")) {
      mobileNav.setAttribute("hidden", "");
      if (navToggle) {
        navToggle.setAttribute("aria-expanded", "false");
        navToggle.focus();
      }
    }
    if (searchPanel && !searchPanel.hasAttribute("hidden")) {
      searchPanel.setAttribute("hidden", "");
      if (searchToggle) {
        searchToggle.setAttribute("aria-expanded", "false");
        searchToggle.focus();
      }
    }
  });
})();
