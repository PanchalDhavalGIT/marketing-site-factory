---
name: seo-optimizer
description: Implement complete on-page SEO including meta tags, Schema.org markup, Open Graph, sitemap.xml, and semantic HTML structure.
---

# SEO Optimizer

Implement comprehensive on-page SEO for a Next.js marketing site.

## Meta Tags (per page)

In the Next.js App Router `metadata` export for each page:

```typescript
export const metadata: Metadata = {
  title: "Page Title | Business Name",      // 50-60 chars
  description: "...",                         // 150-160 chars
  keywords: ["keyword1", "keyword2"],
  openGraph: {
    title: "...",
    description: "...",
    url: "https://domain.com/page",
    siteName: "Business Name",
    type: "website",
    locale: "en_US"
  },
  twitter: {
    card: "summary_large_image",
    title: "...",
    description: "..."
  },
  robots: {
    index: true,
    follow: true
  }
}
```

## Schema.org JSON-LD

Add to the root layout (`app/layout.tsx`):

```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Business Name",
  "description": "...",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "...",
    "addressLocality": "...",
    "addressRegion": "...",
    "postalCode": "..."
  },
  "telephone": "...",
  "email": "...",
  "url": "https://..."
}
```

## Required Files

### `public/sitemap.xml`
Generate from all page routes.

### `public/robots.txt`
```
User-agent: *
Allow: /
Sitemap: https://domain.com/sitemap.xml
```

## Semantic HTML Checklist

- Exactly ONE `<h1>` per page
- Heading hierarchy: h1 → h2 → h3 (no skipping levels)
- All images have descriptive `alt` text (not "image" or "photo")
- Navigation uses `<nav>` with `aria-label`
- Main content in `<main>` tag
- Footer in `<footer>` tag
- Links have descriptive text (not "click here")
- Contact page form has proper `<label>` elements

## Performance SEO

- All images via `next/image` (auto WebP, lazy loading)
- Fonts via `next/font` (no layout shift)
- No render-blocking resources
- Preconnect to Google Fonts if used externally