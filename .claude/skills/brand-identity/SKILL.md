---
name: brand-identity
description: Generate a unique brand identity (colors, fonts, mood) for a business based on its industry and data. Outputs brand.json.
---

# Brand Identity Generator

Generate a complete, unique brand identity for a business marketing site.

## Input

You receive a `brief.json` containing business data and an assigned theme from `templates/themes.json`. Use the theme as a starting point but adapt it to the specific business.

## Process

1. Read `brief.json` for business name, industry, description, services
2. Read the assigned theme from the brief
3. Adapt the theme colors to feel unique to this specific business:
   - Shift hues by 5-15 degrees based on business personality
   - Adjust saturation for the industry (luxury = desaturated, food = vibrant)
   - Ensure WCAG AA contrast ratios (4.5:1 for text, 3:1 for large text)
4. Select Google Fonts pairing:
   - Heading font: personality-driven (e.g., Playfair Display for luxury, Montserrat for tech)
   - Body font: always highly readable (e.g., Inter, Source Sans Pro, Lato)
5. Define visual mood keywords (3-5 words)
6. Define spacing scale (compact, balanced, spacious)

## Output

Write `brand.json` to the workspace root:

```json
{
  "business_name": "...",
  "colors": {
    "primary": "#hex",
    "secondary": "#hex",
    "accent": "#hex",
    "background": "#hex",
    "surface": "#hex",
    "text": "#hex",
    "text_muted": "#hex"
  },
  "fonts": {
    "heading": "Font Name",
    "body": "Font Name",
    "google_import": "@import url('https://fonts.googleapis.com/css2?family=...')"
  },
  "mood": ["keyword1", "keyword2", "keyword3"],
  "spacing": "balanced",
  "border_radius": "md",
  "shadow_style": "subtle"
}
```

## Rules

- NEVER use the exact same hex values from the theme template — always adapt
- NEVER use pure black (#000000) for text — use a dark shade of the primary color
- Ensure primary and accent colors are visually distinct (>30 degree hue difference)
- Test that text colors pass WCAG AA contrast against their intended backgrounds