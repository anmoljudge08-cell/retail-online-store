:root {
  --bg: #f5f7fb;
  --panel: #ffffff;
  --panel-alt: #eef3ff;
  --ink: #172033;
  --muted: #5e6880;
  --accent: #5354d6;
  --accent-strong: #3e40bd;
  --accent-soft: rgba(83, 84, 214, 0.12);
  --green: #1ca774;
  --danger: #d94b49;
  --shadow: 0 18px 40px rgba(20, 30, 58, 0.08);
  --radius: 20px;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  font-family: "Inter", Arial, sans-serif;
  color: var(--ink);
  background: linear-gradient(180deg, #f9fafe 0%, #eef2ff 100%);
}

a {
  color: inherit;
  text-decoration: none;
}

button,
input,
textarea {
  font: inherit;
}

.container {
  width: min(1200px, calc(100% - 32px));
  margin: 0 auto;
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(18px);
  border-bottom: 1px solid rgba(23, 32, 51, 0.06);
}

.header-inner,
.footer-inner,
.catalog-header-row,
.hero-inner,
.section-heading,
.inline-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-inner {
  min-height: 78px;
  gap: 24px;
}

.brand {
  font-size: clamp(1.5rem, 2vw, 2rem);
  font-weight: 800;
  letter-spacing: -0.06em;
}

.brand span {
  color: var(--accent);
}

.main-nav,
.header-actions {
  display: flex;
  align-items: center;
  gap: 18px;
}

.main-nav a {
  color: var(--muted);
  font-weight: 600;
}

.nav-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 0.75rem;
}

.welcome-text {
  color: var(--muted);
  font-weight: 600;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.btn:hover {
  transform: translateY(-1px);
}

.btn-primary {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%);
  color: white;
  box-shadow: 0 12px 28px rgba(83, 84, 214, 0.25);
}

.btn-secondary {
  background: white;
  color: var(--ink);
  border: 1px solid rgba(23, 32, 51, 0.08);
}

.btn-danger {
  background: rgba(217, 75, 73, 0.08);
  color: var(--danger);
}

.btn-small {
  padding: 10px 14px;
  font-size: 0.8rem;
}

.btn-full {
  width: 100%;
  padding: 14px 16px;
}

.hero {
  padding: 70px 0 30px;
}

.hero-inner {
  gap: 32px;
  align-items: center;
  background: linear-gradient(135deg, rgba(83, 84, 214, 0.1), rgba(92, 182, 255, 0.08));
  border-radius: 32px;
  padding: 44px;
  box-shadow: var(--shadow);
}

.hero-copy,
.hero-card {
  flex: 1;
}

.eyebrow {
  display: inline-block;
  color: var(--accent);
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 800;
}

.hero-copy h1 {
  margin: 16px 0;
  font-size: clamp(2.7rem, 5vw, 4.5rem);
  line-height: 1.02;
  letter-spacing: -0.06em;
}

.hero-copy p {
  max-width: 600px;
  margin: 0;
  color: var(--muted);
  font-size: 1.04rem;
  line-height: 1.8;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 22px;
}

.btn,
.hero-actions .btn,
.search-form button,
.auth-form button {
  min-height: 48px;
  padding: 0 18px;
}

.trust-points {
  list-style: none;
  padding: 0;
  margin: 26px 0 0;
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  color: var(--muted);
  font-size: 0.92rem;
}

.trust-points li::before {
  content: "✓";
  color: var(--green);
  margin-right: 8px;
}

.hero-card {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 22px;
}

.mini-card {
  width: min(100%, 340px);
  padding: 26px 20px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(83, 84, 214, 0.08);
  box-shadow: var(--shadow);
}

.mini-label {
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.mini-card h3 {
  margin: 10px 0 14px;
  font-size: 1.7rem;
}

.mini-price-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.mini-price-row strong {
  font-size: 1.6rem;
}

.mini-price-row span {
  padding: 8px 10px;
  border-radius: 999px;
  background: rgba(28, 167, 116, 0.12);
  color: var(--green);
  font-weight: 700;
}

.hero-visual {
  width: 180px;
  height: 180px;
  display: grid;
  place-items: center;
  font-size: 5rem;
  border-radius: 32px;
  background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(83,84,214,0.1));
  border: 1px solid rgba(83, 84, 214, 0.08);
}

.catalog-header,
.page-section,
.auth-section {
  padding: 46px 0 12px;
}

.catalog-header-row {
  gap: 20px;
}

.catalog-header-row h2,
.section-heading h2 {
  margin: 12px 0 0;
  font-size: clamp(2rem, 3vw, 2.8rem);
  letter-spacing: -0.05em;
}

.search-form {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  max-width: 540px;
}

.search-form input,
.auth-form input,
.auth-form textarea,
.checkout-form input,
.checkout-form textarea,
.quantity-form input {
  width: 100%;
  border: 1px solid rgba(23, 32, 51, 0.08);
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  padding: 14px 16px;
  color: var(--ink);
}

.search-form input {
  min-width: 0;
}

.catalog-filters {
  padding: 8px 0 0;
}

.category-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 6px 0 16px;
}

.category-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 10px 16px;
  border-radius: 999px;
  background: rgba(255,255,255,0.7);
  border: 1px solid rgba(23,32,51,0.06);
  color: var(--muted);
  font-weight: 700;
  transition: all 0.2s ease;
}

.category-pill.active,
.category-pill:hover {
  background: var(--accent);
  color: white;
  box-shadow: 0 10px 20px rgba(83,84,214,0.2);
}

.products-section {
  padding: 18px 0 30px;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 22px;
}

.product-card {
  background: var(--panel);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow);
  border: 1px solid rgba(23, 32, 51, 0.05);
}

.product-art {
  min-height: 190px;
  display: grid;
  place-items: center;
  font-size: 5rem;
}

.art-0 { background: linear-gradient(135deg, #edf3ff, #dfe8ff); }
.art-1 { background: linear-gradient(135deg, #fff2ea, #fce9d8); }
.art-2 { background: linear-gradient(135deg, #ebfff5, #d9f8ea); }
.art-3 { background: linear-gradient(135deg, #f6f1ff, #ebe3ff); }
.art-4 { background: linear-gradient(135deg, #fff4dd, #f8e8bd); }
.art-5 { background: linear-gradient(135deg, #ebfbff, #dff7ff); }

.product-body {
  padding: 20px 18px 18px;
}

.product-category {
  margin: 0;
  color: var(--muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  font-size: 0.7rem;
  font-weight: 700;
}

.product-body h3 {
  margin: 12px 0 10px;
  font-size: 1.5rem;
  letter-spacing: -0.04em;
}

.product-description {
  margin: 0;
  min-height: 78px;
  color: var(--muted);
  line-height: 1.7;
}

.product-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 18px;
}

.product-footer strong,
.summary-row strong,
.line-total strong {
  font-size: 1.25rem;
}

.why-us {
  padding: 16px 0 80px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

.feature-grid article {
  padding: 26px 20px;
  border-radius: var(--radius);
  background: rgba(255,255,255,0.8);
  border: 1px solid rgba(23,32,51,0.05);
  box-shadow: var(--shadow);
}

.feature-grid span {
  display: inline-grid;
  place-items: center;
  width: 54px;
  height: 54px;
  border-radius: 16px;
  background: var(--panel-alt);
  font-size: 1.6rem;
}

.feature-grid h3 {
  margin: 16px 0 8px;
  font-size: 1.3rem;
}

.feature-grid p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.empty-state,
.empty-cart,
.auth-card,
.checkout-panel,
.cart-summary,
.delivery-card {
  background: rgba(255,255,255,0.9);
  border-radius: var(--radius);
  border: 1px solid rgba(23,32,51,0.05);
  box-shadow: var(--shadow);
}

.empty-state,
.empty-cart {
  padding: 40px 30px;
  text-align: center;
}

.cart-shell,
.checkout-shell {
  padding-bottom: 60px;
}

.cart-layout,
.checkout-layout {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(260px, 360px);
  gap: 22px;
}

.cart-items {
  display: grid;
  gap: 16px;
}

.cart-item {
  display: grid;
  grid-template-columns: auto minmax(160px, 1fr) minmax(150px, 180px) auto auto;
  align-items: center;
  gap: 18px;
  padding: 18px;
  background: rgba(255,255,255,0.9);
  border: 1px solid rgba(23,32,51,0.05);
  border-radius: 18px;
  box-shadow: var(--shadow);
}

.cart-emoji {
  width: 64px;
  height: 64px;
  display: grid;
  place-items: center;
  font-size: 2rem;
  border-radius: 18px;
  background: var(--panel-alt);
}

.cart-copy h3 {
  margin: 0 0 6px;
  font-size: 1.2rem;
}

.cart-copy p {
  margin: 0;
  color: var(--muted);
}

.quantity-form,
.remove-form {
  display: flex;
  align-items: center;
  gap: 12px;
}

.quantity-form label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: var(--muted);
  font-size: 0.8rem;
}

.quantity-form input {
  max-width: 80px;
}

.cart-summary {
  padding: 22px 20px;
  height: fit-content;
}

.cart-summary h3,
.checkout-panel h3 {
  margin-top: 0;
  font-size: 1.5rem;
}

.summary-row,
.summary-item-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(23,32,51,0.06);
  color: var(--muted);
}

.total-row {
  color: var(--ink);
  font-size: 1.1rem;
  border-bottom: none;
  padding-bottom: 0;
}

.summary-row strong,
.summary-item-row strong {
  color: var(--ink);
}

.auth-shell {
  display: grid;
  place-items: center;
  min-height: calc(100vh - 230px);
}

.auth-card,
.checkout-panel {
  width: min(100%, 560px);
  padding: 34px 28px;
}

.auth-card h2,
.checkout-panel h2 {
  margin: 12px 0 18px;
  font-size: clamp(1.8rem, 3vw, 2.5rem);
  letter-spacing: -0.05em;
}

.auth-form,
.checkout-form {
  display: grid;
  gap: 18px;
}

.auth-form label,
.checkout-form label {
  display: grid;
  gap: 8px;
  color: var(--muted);
  font-weight: 600;
}

.auth-switch {
  margin: 22px 0 0;
  color: var(--muted);
  text-align: center;
}

.auth-switch a {
  color: var(--accent);
  font-weight: 700;
}

.delivery-card {
  padding: 18px 20px;
  color: var(--muted);
  line-height: 1.8;
  margin-bottom: 18px;
}

.delivery-card p {
  margin: 0;
}

.success-banner {
  padding: 18px 20px;
  border-radius: 18px;
  background: rgba(28, 167, 116, 0.12);
  border: 1px solid rgba(28, 167, 116, 0.18);
  color: var(--ink);
}

.success-banner h3 {
  margin-top: 0;
  margin-bottom: 12px;
}

.success-banner p {
  margin: 0 0 8px;
}

.flash-holder {
  margin-top: 18px;
}

.flash {
  padding: 14px 18px;
  border-radius: 12px;
  font-weight: 600;
  margin-bottom: 12px;
}

.flash-success {
  background: rgba(28, 167, 116, 0.12);
  color: #0d7b52;
}

.flash-error {
  background: rgba(217, 75, 73, 0.08);
  color: #a52929;
}

.site-footer {
  border-top: 1px solid rgba(23,32,51,0.06);
  background: rgba(255,255,255,0.5);
  padding: 18px 0 28px;
}

.footer-inner {
  gap: 10px;
  color: var(--muted);
}

@media (max-width: 900px) {
  .product-grid,
  .feature-grid,
  .cart-layout,
  .checkout-layout {
    grid-template-columns: 1fr 1fr;
  }

  .cart-item {
    grid-template-columns: auto 1fr;
  }

  .quantity-form,
  .remove-form,
  .line-total {
    grid-column: 2;
  }

  .cart-summary {
    grid-column: 1 / -1;
  }
}

@media (max-width: 720px) {
  .header-inner,
  .catalog-header-row,
  .hero-inner,
  .inline-heading,
  .footer-inner {
    flex-direction: column;
    align-items: flex-start;
  }

  .main-nav,
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .search-form {
    width: 100%;
    max-width: none;
    flex-direction: column;
    align-items: stretch;
  }

  .product-grid,
  .feature-grid,
  .cart-layout,
  .checkout-layout {
    grid-template-columns: 1fr;
  }

  .hero-card {
    width: 100%;
  }

  .hero-inner {
    padding: 28px 20px;
  }

  .hero-copy h1 {
    font-size: 2.4rem;
  }

  .cart-item {
    grid-template-columns: 1fr;
    text-align: left;
  }

  .quantity-form,
  .remove-form,
  .line-total {
    grid-column: auto;
    width: 100%;
  }

  .quantity-form {
    flex-direction: column;
    align-items: stretch;
  }
}
