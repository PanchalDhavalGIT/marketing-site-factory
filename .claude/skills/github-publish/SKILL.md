---
name: github-publish
description: Create a GitHub repository and push the site code. Follows naming convention marketing-{business-slug}.
allowed-tools: Bash, Read
---

# GitHub Publish

Create a new GitHub repo and push the marketing site code.

## Naming Convention

Repository name: `marketing-{business-slug}`

Where `business-slug` is the business name lowercased, spaces replaced with hyphens, special characters removed.

Example: "Joe's Pizza Palace" → `marketing-joes-pizza-palace`

## Steps

### 1. Initialize Git
```bash
git init
git add .
git commit -m "Initial commit: marketing site for {Business Name}"
```

### 2. Create GitHub Repo
```bash
gh repo create marketing-{slug} --public --source=. --push --description "Marketing site for {Business Name}"
```

### 3. Verify
```bash
gh repo view marketing-{slug} --json url --jq '.url'
```

## Output

Write to `github-result.json`:
```json
{
  "repo_url": "https://github.com/username/marketing-{slug}",
  "status": "success"
}
```

## Error Handling

- Repo already exists → append random 4-digit suffix and retry
- Auth failure → report gh auth status
- Push failure → check for large files, .gitignore issues