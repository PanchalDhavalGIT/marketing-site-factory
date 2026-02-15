---
name: ux-flow
description: Design user experience flow, page structure, navigation hierarchy, and information architecture for multi-page marketing sites.
---

# UX Flow Architecture

Design the complete information architecture and user journey for a marketing site.

## Input

- `brief.json` — business data (name, industry, services, description)
- `research.json` — industry research from researcher agent

## Pages to Design

Every site gets these 5 pages (minimum):

### 1. Home (`/`)
- Hero section with primary value proposition
- 3-4 key services/features overview
- Social proof section (testimonials/stats)
- Primary CTA
- Brief about section teaser

### 2. About (`/about`)
- Business story/mission
- Team or founder section (placeholder if no real data)
- Values or differentiators
- Trust signals (years in business, certifications)

### 3. Services (`/services`)
- Individual service cards with descriptions
- Pricing hints if applicable
- Per-service CTA linking to contact

### 4. Contact (`/contact`)
- Contact form (name, email, phone, message)
- Business address, phone, email display
- Embedded map placeholder
- Business hours if applicable

### 5. Blog (`/blog`)
- 3 placeholder blog post cards
- Each with title, excerpt, date, read-more link
- Individual post template (`/blog/[slug]`)

## Output

Write `sitemap.json`:

```json
{
  "pages": [
    {
      "path": "/",
      "title": "Home",
      "sections": [
        {"type": "hero", "content_zone": "headline, subheadline, cta_button"},
        {"type": "features", "content_zone": "3-4 service cards"},
        {"type": "social_proof", "content_zone": "testimonials or stats"},
        {"type": "cta", "content_zone": "primary conversion action"},
        {"type": "about_teaser", "content_zone": "brief company intro"}
      ]
    }
  ],
  "navigation": {
    "primary": ["Home", "About", "Services", "Blog", "Contact"],
    "cta_button": "Get Started"
  },
  "conversion_goals": ["contact form submission", "phone call", "email inquiry"]
}
```

## UX Principles

- Primary CTA visible above the fold on every page
- Contact info accessible within 2 clicks from any page
- Navigation consistent across all pages
- Mobile navigation: hamburger menu with clear CTA button always visible
- Page load priority: hero content first, below-fold lazy-loaded
- Scroll depth consideration: most important content in first 2 viewport heights