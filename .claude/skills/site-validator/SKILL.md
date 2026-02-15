---
name: site-validator
description: Validate a completed marketing site for build success, SEO completeness, content quality, and basic accessibility before deployment.
allowed-tools: Bash, Read, Glob, Grep
---

# Site Validator

Run quality assurance checks on a completed Next.js marketing site before deployment.

## Checks

### 1. Build Check
```bash
npm run build
```
Must exit 0 with no errors.

### 2. Page Existence
Verify all required pages exist:
- `app/page.tsx` (Home)
- `app/about/page.tsx`
- `app/services/page.tsx`
- `app/contact/page.tsx`
- `app/blog/page.tsx`
- `app/layout.tsx` (Root layout)

### 3. SEO Check
For each page file, verify:
- `metadata` export exists with `title` and `description`
- Title is 50-60 characters
- Description is 150-160 characters
- Root layout has Schema.org JSON-LD script

Check for existence of:
- `public/sitemap.xml`
- `public/robots.txt`

### 4. Content Check
Grep across all page files for:
- NO "Lorem ipsum" (fail if found)
- NO "[Business Name]" or similar unfilled placeholders
- At least one `<h1>` equivalent per page
- Contact page has form elements

### 5. Asset Check
- `tailwind.config.ts` exists and has custom theme colors
- `public/` directory is not empty
- `next.config` exists

## Output

Write `validation-result.json`:
```json
{
  "passed": true,
  "score": 92,
  "checks": {
    "build": {"passed": true},
    "pages": {"passed": true, "found": 6},
    "seo": {"passed": true, "issues": []},
    "content": {"passed": true, "issues": []},
    "assets": {"passed": true}
  },
  "blocking_issues": [],
  "warnings": []
}
```

A site passes validation if `score >= 70` and `blocking_issues` is empty.
Blocking issues: build failure, missing pages, Lorem ipsum text.
Warnings: suboptimal meta tag length, missing sitemap.