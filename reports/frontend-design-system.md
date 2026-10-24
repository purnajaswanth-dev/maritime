# Frontend Design System & Token Specification

**Project:** Where Is My Ferry?  
**Phase:** Complete Professional Frontend Design & Local Implementation  
**Date:** 2026-10-16  
**Document:** Visual Identity, CSS Tokens, Typography Scale, and Accessibility Standards  

---

## 1. Mandatory Color Palette & Token Definitions

All brand, surface, text, border, and status tokens strictly adhere to the project palette specified in Section 5.

### Core Brand Tokens

| Token Name | CSS Custom Variable | Hex Code | Purpose & Accessibility Usage |
|---|---|---|---|
| **Deep Ocean** | `--color-deep-ocean` | `#071B2B` | Primary brand surface, dark navigation header, dark hero backgrounds, high-contrast dark text. |
| **Ocean Blue** | `--color-ocean-blue` | `#0D3045` | Secondary dark surfaces, card headers in dark themes, modal backdrops, elevated dark cards. |
| **Electric Teal** | `--color-electric-teal` | `#14B8A6` | Primary action buttons (with dark text or white on dark containers), active tab underline, highlight tags. |
| **Arctic White** | `--color-arctic-white` | `#F4F8FB` | Main light page background, clean canvas for passenger cards and journey listings. |
| **Sea Mist** | `--color-sea-mist` | `#D8E5ED` | Component borders, card outlines, subtle dividers, neutral table header backgrounds. |
| **Bright Sky Blue**| `--color-sky-blue` | `#38BDF8` | Links, map route polylines, vessel heading vectors, informative badges. |
| **Coral Orange** | `--color-coral-orange` | `#FF8A5B` | Special offers, departure alerts, attention callouts, promotional tags. |

### Semantic Status Tokens

| Token Name | CSS Custom Variable | Hex Code | Intended Use & Contrast Rules |
|---|---|---|---|
| **Success Green** | `--color-success` | `#22C55E` | Confirmed bookings, arrived state, on-time departures. Paired with dark text or icons. |
| **Warning Amber** | `--color-warning` | `#FBBF24` | Delayed voyages, stale telemetry (>600s), weather advisories, low seat availability. |
| **Error Red** | `--color-error` | `#F87171` | Canceled journeys, validation errors, payment failures, terminal closed. |

### Semantic UI Variables

```css
:root {
  /* Brand Foundations */
  --color-brand-primary: #071B2B;       /* Deep Ocean */
  --color-brand-secondary: #0D3045;     /* Ocean Blue */
  --color-action-primary: #14B8A6;      /* Electric Teal */
  --color-action-hover: #0D9488;        /* Teal 600 */
  --color-background: #F4F8FB;          /* Arctic White */
  --color-surface: #FFFFFF;             /* Pure White Card */
  --color-surface-subtle: #EAF1F6;      /* Soft Maritime Tint */
  --color-border: #D8E5ED;              /* Sea Mist */
  --color-border-hover: #94A3B8;        /* Slate 400 */

  /* Typography */
  --color-text-primary: #071B2B;        /* Deep Ocean for maximum readability */
  --color-text-secondary: #475569;      /* Slate 600 for supporting labels */
  --color-text-muted: #64748B;          /* Slate 500 for timestamps & captions */
  --color-text-inverse: #FFFFFF;        /* Pure white on dark surfaces */
  --color-link: #0284C7;                /* High contrast Sky/Ocean link */

  /* Status Tokens */
  --color-success: #16A34A;             /* WCAG AA Compliant Green */
  --color-success-bg: #DCFCE7;          /* Soft green tint */
  --color-warning: #D97706;             /* WCAG AA Compliant Amber */
  --color-warning-bg: #FEF3C7;          /* Soft amber tint */
  --color-error: #DC2626;               /* WCAG AA Compliant Red */
  --color-error-bg: #FEE2E2;            /* Soft red tint */
  --color-info: #0284C7;                /* Sky Blue 600 */
  --color-info-bg: #E0F2FE;             /* Sky blue tint */

  /* Accents */
  --color-accent-coral: #FF8A5B;        /* Coral Orange */
  --color-accent-coral-bg: #FFF0EB;

  /* Elevation Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(7, 27, 43, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(7, 27, 43, 0.08), 0 2px 4px -2px rgba(7, 27, 43, 0.04);
  --shadow-lg: 0 10px 15px -3px rgba(7, 27, 43, 0.10), 0 4px 6px -4px rgba(7, 27, 43, 0.05);
  --shadow-card: 0 2px 8px -2px rgba(7, 27, 43, 0.06), 0 0 0 1px #D8E5ED;

  /* Radii */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-full: 9999px;
}
```

---

## 2. Typography & Numerical Formatting

- **Font Family:** `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- **Tabular Numerals:** For ETA countdowns, timestamps, prices, and speed figures:
  ```css
  .tabular-nums {
    font-variant-numeric: tabular-nums;
    font-feature-settings: "tnum";
  }
  ```
- **Type Scale:**
  - **Display (Hero Headline):** `36px – 48px` / Bold (700)
  - **Page Title (`h1`):** `28px – 32px` / Bold (700)
  - **Section Heading (`h2`):** `22px – 24px` / SemiBold (600)
  - **Card Heading (`h3`):** `18px – 20px` / SemiBold (600)
  - **Body Primary:** `15px – 16px` / Regular (400)
  - **Body Secondary:** `13px – 14px` / Regular (400)
  - **Caps / Micro Labels:** `11px – 12px` / Medium (500) / Tracking +0.05em

---

## 3. Component Design Rules

1. **Buttons:**
   - `Primary`: Background `--color-action-primary` (`#14B8A6`), Text `#071B2B` or `#FFFFFF` (high contrast), Hover `#0D9488`.
   - `Secondary`: Background white, Border `--color-border` (`#D8E5ED`), Text `--color-brand-primary`.
   - `Ghost`: Transparent background, hover background `--color-surface-subtle`.
   - `Danger`: Background `--color-error`, Text white.
   - Height: Standard 42px (md), 34px (sm), 48px (lg).

2. **Status Badges:**
   - Always combines icon + text + colored background pill. Never relies on color alone.
   - `ESTIMATING`: Blue/Teal badge with pulsing radar indicator.
   - `ARRIVED`: Green badge with checkmark.
   - `DELAYED_OR_UNCERTAIN`: Amber badge with alert triangle.
   - `STALE_DATA`: Slate/amber badge with clock alert.

3. **Accessibility Standards (WCAG 2.1 AA):**
   - High contrast ratios: Deep Ocean (`#071B2B`) on white is 16.5:1 (exceeds 4.5:1 requirement).
   - Interactive focus states: Visible 2px outline in `--color-action-primary`.
   - Explicit `aria-label`s on map zoom, swap-route button, and mobile menu toggles.
