---
name: cx-strategy
description: Audit the complete customer experience of a marketing site - first impressions, trust signals, conversion path, friction points, and mobile experience.
---

# Customer Experience Strategist

Review a built marketing site from the perspective of a first-time visitor who is a potential customer.

## Audit Checklist

### First Impression (0-3 seconds)
- [ ] Is the business name/logo immediately visible?
- [ ] Can the visitor understand what the business does within 3 seconds?
- [ ] Is the primary value proposition above the fold?
- [ ] Does the visual design feel professional and trustworthy?

### Trust Signals
- [ ] Real business address displayed
- [ ] Phone number visible (ideally in header)
- [ ] Professional email (not gmail/yahoo)
- [ ] Testimonials or reviews present
- [ ] Years in business or client count mentioned
- [ ] No broken images or placeholder content

### Conversion Path
- [ ] Primary CTA visible on homepage without scrolling
- [ ] CTA appears at least once more below the fold
- [ ] Contact page is one click from any page
- [ ] Phone number is clickable (tel: link) on mobile
- [ ] Email is clickable (mailto: link)
- [ ] Contact form is simple (4-5 fields max)

### Navigation & Usability
- [ ] All nav links work correctly
- [ ] Current page is indicated in navigation
- [ ] User can get back to home from any page
- [ ] No dead ends (every page has a next action)
- [ ] 404 page is helpful (not default)

### Mobile Experience
- [ ] Site is readable on 375px width
- [ ] Touch targets are at least 44px
- [ ] No horizontal scrolling
- [ ] Navigation works on mobile (hamburger/drawer)
- [ ] CTA button accessible without scrolling far
- [ ] Images scale properly

### Content Quality
- [ ] No "Lorem ipsum" or placeholder text
- [ ] No "[Business Name]" unfilled variables
- [ ] Spelling and grammar are correct
- [ ] Tone matches the industry
- [ ] All services from brief.json are represented

## Output

Write `cx-review.json`:

```json
{
  "score": 85,
  "pass": true,
  "issues": [
    {"severity": "high", "area": "trust", "issue": "...", "fix": "..."},
    {"severity": "medium", "area": "mobile", "issue": "...", "fix": "..."}
  ],
  "strengths": ["...", "..."]
}
```

A score below 70 means the site needs fixes before deployment.