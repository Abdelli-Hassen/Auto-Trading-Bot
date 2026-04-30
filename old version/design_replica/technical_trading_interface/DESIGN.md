---
name: Technical Trading Interface
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#bdc8d1'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#87929a'
  outline-variant: '#3e484f'
  surface-tint: '#7bd0ff'
  primary: '#8ed5ff'
  on-primary: '#00354a'
  primary-container: '#38bdf8'
  on-primary-container: '#004965'
  inverse-primary: '#00668a'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#ffbcb7'
  on-tertiary: '#68000a'
  tertiary-container: '#ff938c'
  on-tertiary-container: '#8d0012'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#c4e7ff'
  primary-fixed-dim: '#7bd0ff'
  on-primary-fixed: '#001e2c'
  on-primary-fixed-variant: '#004c69'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffdad7'
  tertiary-fixed-dim: '#ffb3ad'
  on-tertiary-fixed: '#410004'
  on-tertiary-fixed-variant: '#930013'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  display-xl:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  heading-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
  data-lg:
    fontFamily: JetBrains Mono
    fontSize: 18px
    fontWeight: '500'
    lineHeight: '1.2'
  data-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.2'
  data-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  gutter: 12px
  margin: 24px
---

## Brand & Style

This design system is engineered for high-frequency trading environments where precision, speed, and information density are paramount. The brand personality is clinical, authoritative, and unapologetically technical, catering to professional analysts and traders who require zero-latency visual processing.

The aesthetic blends **Minimalism** with **Glassmorphism** accents. While the core structure relies on a rigid, high-contrast grid, glassmorphism is utilized sparingly for overlays and floating panels to maintain a sense of depth without sacrificing legibility. The style emphasizes "function over form," using crisp 1px borders to define information architecture rather than heavy shadows or decorative elements. The result is a high-performance dashboard that feels like a sophisticated cockpit.

## Colors

The color palette is optimized for a dark-mode-first experience to reduce eye strain during extended sessions. The foundation is built on a deep navy-charcoal (#0F172A), providing a high-contrast base for data visualization. 

- **Primary Action (#38BDF8):** A bright cyan used for active states, primary buttons, and navigational highlights.
- **Success/Positive (#10B981):** A vibrant green reserved strictly for profitable trends, "buy" orders, and active system statuses.
- **Danger/Negative (#EF4444):** A sharp red for price drops, "sell" orders, and critical alerts.
- **Neutral/Surface:** Secondary surfaces use #1E293B, with borders defined by #334155 to create subtle but clear containment.

Color is used functionally: if a pixel is colored, it must convey specific meaning (direction, priority, or interactivity).

## Typography

This design system employs a dual-font strategy. **Inter** handles all UI scaffolding, labels, and instructional text, providing institutional clarity and readability at small scales. **JetBrains Mono** is used exclusively for numerical data, tickers, and code-like values. The monospaced nature of JetBrains Mono ensures that shifting digits in live-price updates do not cause horizontal layout "jitter," maintaining visual stability during high volatility.

Text hierarchy is tightly controlled. Use `label-caps` for table headers and metadata categories. `data-md` is the workhorse for price feeds, while `display-xl` is reserved for total portfolio balances or critical high-level metrics.

## Layout & Spacing

The layout utilizes a **fluid 12-column grid** designed for 1440px+ screens, favoring a high-density information display. The rhythm is based on a **4px base unit**, allowing for extremely tight spacing required for complex trading terminals.

- **Gutters:** 12px gutters provide just enough separation between data panels without wasting valuable screen real estate.
- **Margins:** 24px outer margins frame the primary dashboard.
- **Density:** Components should prioritize vertical compactness. Data rows in tables should use `sm` (8px) padding to maximize the number of visible records on a single fold.

## Elevation & Depth

Hierarchy is established through **tonal layering** and **crisp borders** rather than traditional shadows. In this design system, "higher" elements are represented by lighter background fills and more pronounced border colors.

1.  **Base Layer:** #0F172A (The background).
2.  **Surface Layer:** #1E293B (Cards, panels, and widgets).
3.  **Accent Layer (Glassmorphism):** Modals and dropdown menus use a semi-transparent version of the surface color with a 12px backdrop-blur and a 1px solid border (#334155). This creates a "heads-up display" (HUD) effect, allowing the user to maintain context of the data moving underneath the overlay.

Shadows are avoided entirely to keep the UI feeling sharp and technical.

## Shapes

The shape language is strictly geometric. To evoke a sense of precision and technical rigor, the design system uses **subtly rounded corners (4px)**. This provides a modern touch while maintaining the "sharpness" requested for a professional trading tool.

- **Buttons & Inputs:** 4px radius.
- **Cards & Panels:** 4px radius.
- **Tags/Chips:** 2px or 4px radius (never pill-shaped).
- **Data Markers:** 0px (sharp) for chart indicators to ensure they align perfectly with pixel grids.

## Components

### Buttons
Primary buttons use the Cyan (#38BDF8) fill with black or dark navy text for maximum contrast. Secondary buttons use a "ghost" style: 1px border of the primary color with no fill. "Buy" and "Sell" buttons use the Green and Red primary colors respectively.

### Data Tables
Tables are the core of this design system. Use `data-sm` for rows. Row separators are 1px solid #334155. Hover states should use a subtle highlight (#1E293B) to guide the eye across wide data sets.

### Input Fields
Inputs are dark-filled (#0F172A) with a 1px border. When focused, the border glows with the Cyan primary color and a very subtle outer glow (0px 0px 4px).

### Cards & Panels
Panels are used to house widgets (charts, order books). Every panel must have a 1px border. Panel headers use the `label-caps` typography and are separated from the content by a 1px horizontal rule.

### Chips/Indicators
Used for "Market Open," "Live," or "Halted" status. These are small, square-cornered labels with a background tint matching their status color (e.g., 10% opacity Green for "Live" status).

### Trading Specifics
- **Order Book:** Alternating red/green text for Bid/Ask prices using monospaced fonts.
- **Price Tickers:** Use a small triangle icon (up/down) next to price changes to provide redundant signaling alongside color.
