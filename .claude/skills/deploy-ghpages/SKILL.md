---
name: deploy-ghpages
description: Deploy a Next.js static marketing site to GitHub Pages. Handles static export, GitHub repo creation, GitHub Actions workflow, and Pages activation.
allowed-tools: Bash, Read, Write
---

# GitHub Pages Deployment

Deploy a completed Next.js site as a static export to GitHub Pages.

## Prerequisites

- `GITHUB_TOKEN` environment variable set (with repo and pages permissions)
- Site builds successfully with `npm run build` (static export)
- `next.config` has `output: 'export'` set

## Steps

### 1. Configure Next.js for Static Export
Ensure `next.config.mjs` or `next.config.ts` contains:
```js
const nextConfig = {
  output: 'export',
  images: { unoptimized: true },
};
```
This generates a static `out/` directory instead of a server build.

### 2. Build Static Site
```bash
npm run build
```
Verify `out/` directory exists with HTML files.

### 3. Create GitHub Repo and Push
```bash
git init
git add .
git commit -m "Initial commit: marketing site for {Business Name}"
gh repo create marketing-{slug} --public --source=. --push --description "Marketing site for {Business Name}"
```

### 4. Create GitHub Actions Workflow
Write `.github/workflows/deploy.yml`:
```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run build
      - uses: actions/upload-pages-artifact@v3
        with:
          path: out
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

### 5. Enable GitHub Pages via API
```bash
gh api repos/{owner}/{repo}/pages -X POST -f build_type=workflow
```

### 6. Push Workflow to Trigger Deploy
```bash
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Pages deployment workflow"
git push
```

### 7. Wait for Deployment and Get URL
The site will be live at: `https://{owner}.github.io/marketing-{slug}/`

Verify with:
```bash
gh api repos/{owner}/{repo}/pages --jq '.html_url'
```

## Output

Write deployment info to `deploy-result.json`:
```json
{
  "github_url": "https://github.com/{owner}/marketing-{slug}",
  "pages_url": "https://{owner}.github.io/marketing-{slug}/",
  "status": "success",
  "deployed_at": "ISO timestamp"
}
```

## Error Handling

- Build failure → report specific error, do NOT attempt deployment
- Repo name conflict → append 4 random digits
- Pages enable failure → may need to wait for first workflow run
- Auth failure → report GITHUB_TOKEN permissions issue