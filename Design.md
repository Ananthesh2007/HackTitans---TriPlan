---
version: alpha
name: Hitit Air Travel Dark
description: A high-contrast, aviation-oriented dark system with bold typography, bright white text, and a restrained red accent.
colors:
  primary: "#A01D26"
  secondary: "#FFFFFF"
  tertiary: "#1B1C1D"
  neutral: "#1A1A1A"
  surface: "#252831"
  on-surface: "#FFFFFF"
  error: "#D13B45"
typography:
  headline-display:
    fontFamily: Urbanist
    fontSize: 64px
    fontWeight: 900
    lineHeight: 1.4
    letterSpacing: 0.5px
  headline-lg:
    fontFamily: Urbanist
    fontSize: 48px
    fontWeight: 900
    lineHeight: 1.2
    letterSpacing: 0.5px
  headline-md:
    fontFamily: Urbanist
    fontSize: 24px
    fontWeight: 900
    lineHeight: 1.4
    letterSpacing: 0.5px
  headline-sm:
    fontFamily: Urbanist
    fontSize: 18px
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: 0.5px
  body-lg:
    fontFamily: Urbanist
    fontSize: 18px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0.5px
  body-md:
    fontFamily: Urbanist
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0.5px
  body-sm:
    fontFamily: Urbanist
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: 0.5px
  label-lg:
    fontFamily: Urbanist
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: 0.5px
  label-md:
    fontFamily: Urbanist
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: 0.5px
  label-sm:
    fontFamily: Urbanist
    fontSize: 12px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: 0.5px
rounded:
  none: 0px
  sm: 4px
  md: 8px
  lg: 30px
  xl: 32px
  full: 9999px
spacing:
  xs: 8px
  sm: 16px
  md: 50px
  lg: 90px
  xl: 120px
components:
  button-primary:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.primary}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.xl}"
    padding: 15px 35px
    height: 49px
  button-primary-hover:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.secondary}"
    rounded: "{rounded.xl}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.secondary}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.xl}"
    padding: 15px 35px
    height: 49px
  button-link:
    backgroundColor: "transparent"
    textColor: "{colors.secondary}"
    typography: "{typography.body-md}"
    rounded: "{rounded.none}"
    padding: 0px
  card:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.secondary}"
    rounded: "{rounded.lg}"
    padding: 60px
  input:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.secondary}"
    typography: "{typography.body-md}"
    rounded: "{rounded.md}"
    padding: 16px
  chip:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.secondary}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.full}"
    padding: 8px 12px
---

# Hitit Air Travel Dark

## Overview
This system feels bold, premium, and operationally focused, with a strong aviation identity. It is designed for a corporate travel audience that needs clarity, trust, and quick scanning rather than decorative flourish. The mood is spacious but dramatic: large type, strong contrast, and minimal chrome keep the interface feeling modern and authoritative.

## Colors
- **Primary (#A01D26):** A deep aviation red used as the brand accent for emphasis, active states, and small high-salience details. It should feel restrained rather than loud.
- **Secondary (#FFFFFF):** Pure white used for primary text, button fills, and key contrast moments against the dark UI.
- **Tertiary (#1B1C1D):** A near-black surface tone used for cards and elevated panels so they separate subtly from the page background.
- **Neutral (#1A1A1A):** The main backdrop color for the site, creating the dark stage that makes the typography and accent color stand out.
- **Surface (#252831):** A cool dark surface tone suitable for overlays, cookie banners, and utility containers that need slightly more separation than the base background.
- **On-surface (#FFFFFF):** The default content color on dark surfaces, ensuring maximum legibility.
- **Error (#D13B45):** A clear alert red reserved for destructive actions or validation states; it should remain close to the brand accent but be distinct enough for system meaning.

## Typography
Urbanist is the core typeface across the experience, with very heavy headline weights and compact letter-spacing that give the brand a modern, engineered feel. Headlines are assertive and large: `headline-display` and `headline-lg` are used for hero statements and key page messaging, while `headline-md` supports section titles and prominent content blocks. Body text stays clean and readable at 16px with a comfortable line-height, and labels use semibold weight to maintain clarity on buttons and navigation. The visible style keeps letter-spacing slightly open and avoids all-caps treatment, favoring readability over promotional shouting.

## Layout & Spacing
The layout is built around broad, open composition with clear visual axes rather than dense modular grids. Large spacing values are a defining characteristic: use `xs` and `sm` for internal control gaps, while `md`, `lg`, and `xl` reserve substantial breathing room for hero sections, page-level separation, and large content bands. Panels and overlays feel generously padded, with 60px card padding as a strong reference point. Vertical composition should stay airy and directional, with strong alignment lines and minimal ornamental interruption.

## Elevation & Depth
Depth is subtle and mostly tonal rather than shadow-heavy. The page background is flat and dark, while cards and utility containers rely on slightly lighter surface colors to create hierarchy. Shadows, when used, should be soft and restrained, echoing the existing low-contrast lift of the cookie panel instead of adding glossy or floating effects. Borders are generally minimal or absent; contrast comes from color layering and spacing, not from heavy outlines.

## Shapes
The shape language is smooth and rounded, with pills and large radii dominating the interface. Buttons use an approximately 32px radius, giving them a friendly yet premium capsule shape, while cards sit on a 30px radius for a soft, polished container feel. Smaller UI elements can use modest rounding, but sharp corners should be avoided except for purely structural dividers and link-style text. Overall, the system feels approachable and refined rather than technical or angular.

## Components
Buttons are the most distinctive interactive element. `button-primary` should be a white pill with red text, used for the most important action; it is medium-large, with generous horizontal padding and a 49px minimum height. `button-secondary` should invert the treatment conceptually: transparent background, white text, and a white border, preserving the same rounded pill shape and sizing. `button-link` is reserved for low-emphasis actions and inline legal/help content, using underlined text with no container styling.

Cards should use the `card` treatment: dark surface, white text, 60px padding, and a soft shadow only if separation is needed. Keep card content simple and high-contrast, with strong typographic hierarchy and minimal decoration. Inputs should match the dark surface language with clear white text and rounded corners; focus states should rely on contrast and accent color rather than heavy glow. Chips and small tags should use the primary red with white text and full rounding, keeping them compact and unmistakably interactive. Lists, notices, and consent banners should stay functional and dense enough for long-form legal text, but never visually compete with the main hero treatment.

## Do's and Don'ts
- Do use large, bold Urbanist headlines to maintain the brand’s aviation-grade confidence.
- Do keep text white on dark surfaces for maximum contrast and fast scanning.
- Do use the red accent sparingly for primary actions, highlights, and small brand moments.
- Do prefer rounded pills and soft cards over sharp, technical geometry.
- Do keep surfaces layered tonally, not through heavy shadows or glossy effects.
- Don't introduce bright secondary accent colors that dilute the red-and-charcoal palette.
- Don't reduce headline weight or size; the system depends on strong typographic presence.
- Don't crowd sections with small spacing or dense groupings that break the open, premium feel.