---
name: ui-design
description: Design UI components and visual layout for marketing site pages using Tailwind CSS. Uses brand.json for styling decisions.
---

# UI Design System

Design the visual component layer for a multi-page marketing site using Tailwind CSS.

## Input

- `brand.json` — color palette, fonts, mood, spacing
- `sitemap.json` — page structure and content zones
- `design-spec.json` — if already created by ui-designer agent

## Component Library

Design these component types using Tailwind utility classes:

### Hero Sections (pick ONE per site — variety is critical)
- **Split hero**: Image left/right + text opposite side
- **Full-bleed hero**: Background image with overlay text
- **Gradient hero**: Animated gradient background with centered text
- **Video hero**: Background video placeholder with overlay
- **Minimal hero**: Large typography, no image, bold statement

### Feature/Service Sections
- **Card grid**: 3-column cards with icons
- **Alternating rows**: Image + text alternating sides
- **Icon list**: Vertical list with descriptive icons
- **Tabbed features**: Tab-based feature showcase

### Social Proof
- **Testimonial carousel**: Rotating quotes
- **Review cards**: Grid of customer review cards
- **Stats bar**: Key numbers in a horizontal bar
- **Logo wall**: Client/partner logos

### CTA Sections
- **Banner CTA**: Full-width colored banner
- **Card CTA**: Centered card with action
- **Floating CTA**: Sticky bottom bar on mobile

### Navigation
- **Classic navbar**: Logo left, links right, CTA button
- **Centered navbar**: Logo center, links split
- **Hamburger**: Mobile-first with slide-out menu

### Footer
- **4-column footer**: Links organized by category
- **Simple footer**: Single row with essentials
- **CTA footer**: Newsletter signup + links

## Rules

- Map all colors to Tailwind config via `brand.json` values
- Use `tailwind.config.js` extend section for custom colors/fonts
- Mobile-first: design for 375px, then scale up
- Minimum touch target: 44x44px for interactive elements
- Consistent spacing: use the brand's spacing scale throughout
- Every section needs vertical padding of at least `py-16` (desktop) / `py-12` (mobile)
- Images use `next/image` with proper width/height/alt
- NEVER use inline styles — Tailwind utilities only