---
name: ui-design
description: Design ultra-modern, Awwwards-quality UI using Tailwind CSS. Uses brand.json + UI/UX Pro Max design system for styling decisions.
---

# UI Design System — Awwwards Quality

Design the visual component layer for a multi-page marketing site using Tailwind CSS. The goal is an ultra-modern, clean, sleek website that looks like it belongs on Awwwards.

## Step 1: Generate Design System (REQUIRED)

Before any design decisions, run the UI/UX Pro Max design system generator:
```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<industry> <keywords>" --design-system -p "<Project Name>"
```

Then get stack-specific guidelines:
```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "layout responsive animation" --stack html-tailwind
```

## Input

- Design system output from Step 1
- `brand.json` — color palette, fonts, mood, spacing
- `sitemap.json` — page structure and content zones

## Awwwards Design Standards

### Visual Quality
- Floating glass navbar: `backdrop-blur-xl bg-white/80` with subtle border
- Smooth scroll behavior: `scroll-smooth` on html element
- Generous section padding: py-20 to py-32, large gaps between sections
- Hero: large bold typography (text-5xl to text-7xl), gradient text or accent highlights
- Cards: subtle shadows, rounded-2xl to rounded-3xl, hover:shadow-xl transitions
- Gradient accents: subtle gradients on backgrounds, buttons, or text highlights
- Whitespace: generous — let the design breathe
- Typography: clear hierarchy (base → lg → 2xl → 4xl → 6xl)
- Container: max-w-7xl mx-auto with px-4 to px-6

### Micro-Animations
- hover:scale-[1.02] on cards and buttons
- hover:-translate-y-1 on cards for lift effect
- transition-all duration-300 on all interactive elements
- Smooth color transitions on hover states (150-300ms)

### Component Library

#### Hero Sections (pick ONE — make it stunning)
- **Gradient hero**: Animated gradient background, oversized typography, floating glass CTA
- **Split hero**: Image with rounded corners + text, subtle parallax feel
- **Full-bleed hero**: Background with gradient overlay, centered bold text
- **Minimal hero**: Massive typography, no image, bold statement with accent color

#### Feature/Service Sections
- **Card grid**: 3-column cards with SVG icons, hover lift + shadow
- **Bento grid**: Modern bento-style asymmetric grid layout
- **Alternating rows**: Image + text alternating sides with scroll reveal feel

#### Social Proof
- **Testimonial cards**: Glass-effect cards with avatar, quote, rating
- **Stats counter**: Animated numbers in a horizontal bar
- **Logo wall**: Grayscale → color on hover client logos

#### CTA Sections
- **Gradient CTA**: Full-width gradient banner with glass button
- **Card CTA**: Floating centered card with rounded corners and shadow

#### Navigation
- **Floating glass navbar**: Sticky, top-4 inset, backdrop-blur-xl, rounded-2xl, shadow-lg
- Mobile: hamburger with smooth slide-in menu

#### Footer
- **Modern footer**: Multi-column with social links, newsletter input, subtle top border

## Rules

- NEVER use emojis as icons — use inline SVGs only (Heroicons/Lucide style)
- cursor-pointer on ALL clickable/hoverable elements
- Color contrast: 4.5:1 minimum ratio (accessibility)
- Touch targets: minimum 44x44px
- Mobile-first: design for 375px, 768px, 1024px, 1440px
- All transitions: 150-300ms duration
- Line height: 1.5-1.75 for body text
- Line length: max 65-75 characters per line
- prefers-reduced-motion: respect this media query
- NEVER use inline styles — Tailwind utilities only