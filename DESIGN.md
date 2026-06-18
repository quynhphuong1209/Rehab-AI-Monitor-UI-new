---
version: alpha
name: Rehab AI Monitor
description: Clinical rehabilitation monitoring UI with a Rehab blue identity and Antigravity-style data workspace.
colors:
  primary: "#0F172A"
  secondary: "#475569"
  tertiary: "#256ED9"
  accent: "#0284C7"
  success: "#059669"
  warning: "#D97706"
  danger: "#DC2626"
  neutral: "#F8FAFC"
  card: "#FFFFFF"
  terminal: "#0B0F19"
  border: "#D6E1F0"
  dark-surface: "#101A29"
typography:
  display:
    fontFamily: "Fraunces, Georgia, serif"
    fontSize: 52px
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: 0px
  headline:
    fontFamily: "Fraunces, Georgia, serif"
    fontSize: 28px
    fontWeight: 700
    lineHeight: 1.18
    letterSpacing: 0px
  body:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: 0px
  label:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: 13px
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: 0px
  mono:
    fontFamily: "JetBrains Mono, Fira Code, monospace"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1.45
    letterSpacing: 0px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
rounded:
  sm: 8px
  md: 12px
  lg: 20px
  full: 999px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.card}"
    rounded: "{rounded.sm}"
    padding: 12px
  card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: 16px
  input:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: 12px
  active-tab:
    backgroundColor: "#E8F2FF"
    textColor: "#1E5FC4"
    rounded: "{rounded.full}"
    padding: 8px
  link:
    backgroundColor: "transparent"
    textColor: "{colors.accent}"
    rounded: "{rounded.sm}"
    padding: 4px
  status-success:
    backgroundColor: "#E9FBF3"
    textColor: "#065F46"
    rounded: "{rounded.full}"
    padding: 6px
  status-warning:
    backgroundColor: "#FFF7E8"
    textColor: "#92400E"
    rounded: "{rounded.full}"
    padding: 6px
  status-danger:
    backgroundColor: "#FEECEC"
    textColor: "#991B1B"
    rounded: "{rounded.full}"
    padding: 6px
  terminal-log:
    backgroundColor: "{colors.terminal}"
    textColor: "#38BDF8"
    rounded: "{rounded.sm}"
    padding: 16px
  dark-panel:
    backgroundColor: "{colors.dark-surface}"
    textColor: "#E5EDF7"
    rounded: "{rounded.sm}"
    padding: 16px
  bordered-card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: 16px
  divider:
    backgroundColor: "{colors.border}"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: 4px
---

# Rehab AI Monitor UI Design System

## Overview

Rehab AI Monitor is a clinical rehabilitation workspace. The interface should feel trustworthy, precise, and calm: a medical dashboard with enough warmth to support patients, doctors, technicians, researchers, and administrators.

The source of truth for the visual mood is `rehab_ai_monitor_demo.html`: blue clinical CTAs, white cards on a pale blue workspace, compact pill navigation, serif display headlines on the login screen, and Inter for operational UI.

## Colors

- **Primary (#0F172A):** deep slate for main text, headers, and dense table content.
- **Secondary (#475569):** muted labels, descriptions, and metadata.
- **Tertiary (#256ED9):** Rehab blue for CTAs, active tabs, role badges, focus rings, and medical interaction states.
- **Accent (#0284C7):** supporting sky blue for links and secondary active states.
- **Neutral (#F8FAFC):** clean workspace base for data-heavy screens.
- **Card (#FFFFFF):** panels, login cards, metric cards, tables, and repeated patient cards.
- **Terminal (#0B0F19):** raw logs and metadata blocks.

Dark mode uses the same blue accent language, with dark panels and transparent icon wells so input icons never render as white boxes.

## Typography

Display typography uses Fraunces or Georgia for the login hero and high-level branded headings. Operational screens use Inter for clear Vietnamese readability, table scanning, and compact data cards.

Do not scale font sizes directly with viewport width. Use responsive layout widths and line breaks instead.

## Layout

Spacing follows a 4px/8px grid. Large page regions use 24px gaps. Form inputs use `12px 16px` padding. Cards and tables use an 8px radius unless a login card or modal intentionally needs a larger radius.

All role tabs live horizontally in the topbar. Drawer navigation is secondary and must always be reopenable with a visible menu button.

## Elevation & Depth

Use subtle shadows only for cards, the login form, and floating shell controls. Avoid decorative blobs and one-note gradients. Backgrounds should stay quiet so clinical data remains the focus.

## Shapes

Cards use 8px radius for dense dashboard content. Pills use full radius for role chips, nav tabs, and small demo actions. Login forms can use a softer 20px radius to match the demo.

## Components

- **Topbar:** fixed to the top, brand on the left, horizontal role tabs in the center, user and controls on the right.
- **Drawer:** slide-in navigation with active item and summary stats, persisted with localStorage.
- **Auth forms:** match the demo HTML: segmented login/register tabs, role cards with icons, clean inputs, blue CTA, compact demo role pills.
- **Tables:** use avatar initials, status chips, ROM/VAS columns, and right arrow actions.
- **Cards:** show one clear number or patient summary per card; avoid nested cards.
- **Inputs:** show icons with transparent/dark-safe wells; focus ring uses Rehab blue.
- **Logs:** use mono font on terminal background with high-contrast text.

## Do's and Don'ts

- Do keep Rehab blue as the primary visual identity.
- Do keep role dashboards data-centric and compact.
- Do use icons for actions and role identity.
- Do keep mobile auth and patient lists stacked without overlapping.
- Do not move topbar tabs into vertical Streamlit buttons.
- Do not put passwords or secrets in query params.
- Do not allow dark mode input icons to appear inside white squares.
