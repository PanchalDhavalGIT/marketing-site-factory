"""Manages Claude Code CLI session lifecycle — launch, monitor, timeout, retry."""

import asyncio
import json
import os
import time
from pathlib import Path

from orchestrator.config import (
    CLAUDE_CMD,
    CLAUDE_MAX_TURNS,
    DEFAULT_SESSION_TIMEOUT,
    LOGS_DIR,
)
from orchestrator.logger import get_site_logger


class SessionResult:
    """Result of a Claude Code session."""

    def __init__(
        self,
        success: bool,
        output: str = "",
        error: str = "",
        timed_out: bool = False,
    ):
        self.success = success
        self.output = output
        self.error = error
        self.timed_out = timed_out


async def launch_session(
    workspace: Path,
    prompt: str,
    timeout: int = DEFAULT_SESSION_TIMEOUT,
    site_slug: str = "",
    progress_callback=None,
) -> SessionResult:
    """
    Launch a Claude Code CLI session in the given workspace.
    Streams stdout to log file in real-time for dashboard visibility.

    Args:
        workspace: Path to the isolated workspace directory.
        prompt: The prompt to send to Claude Code.
        timeout: Maximum seconds before killing the session.
        site_slug: For logging purposes.
        progress_callback: async callable(slug, phase_msg) for live updates.

    Returns:
        SessionResult with success/failure and output.
    """
    logger = get_site_logger(site_slug or workspace.name)
    slug = site_slug or workspace.name

    cmd = [
        CLAUDE_CMD,
        "-p",  # Print mode (non-interactive)
        prompt,
        "--output-format", "stream-json",  # Stream JSON events for real-time monitoring
        "--max-turns", str(CLAUDE_MAX_TURNS),
        "--dangerously-skip-permissions",
    ]

    env = os.environ.copy()
    env["HOME"] = os.environ.get("HOME", "")

    logger.info(f"Launching Claude session in {workspace}")
    logger.debug(f"CLI flags: --output-format stream-json --max-turns {CLAUDE_MAX_TURNS} --dangerously-skip-permissions")
    logger.debug(f"Prompt length: {len(prompt)} chars")

    # Prepare live log file for streaming (clear previous run)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    live_log = LOGS_DIR / f"{slug}.live.log"
    live_log.write_text("")  # Clear previous run

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(workspace),
            env=env,
        )

        stdout_lines = []
        stderr_lines = []
        start_time = time.time()

        async def read_stream(stream, collector, is_stderr=False):
            """Read stream line-by-line, parse stream-json events, write to live log."""
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").rstrip()
                if not decoded:
                    continue
                collector.append(decoded)

                # Parse stream-json events for human-readable live log
                display_line = _parse_stream_event(decoded) if not is_stderr else decoded

                if display_line:
                    # Write to live log file for dashboard
                    with open(live_log, "a") as f:
                        elapsed = int(time.time() - start_time)
                        prefix = "ERR" if is_stderr else "OUT"
                        f.write(f"[{elapsed:>4}s] [{prefix}] {display_line}\n")

                # Detect phase changes from output and fire callback
                if progress_callback and not is_stderr:
                    phase = _detect_phase(decoded)
                    if phase:
                        await progress_callback(slug, phase)

        try:
            await asyncio.wait_for(
                asyncio.gather(
                    read_stream(process.stdout, stdout_lines),
                    read_stream(process.stderr, stderr_lines, is_stderr=True),
                    process.wait(),
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            elapsed = int(time.time() - start_time)
            logger.warning(f"Session timed out after {elapsed}s — killing process")
            process.kill()
            await process.wait()
            return SessionResult(
                success=False,
                error=f"Session timed out after {timeout} seconds",
                timed_out=True,
            )

        stdout = "\n".join(stdout_lines)
        stderr = "\n".join(stderr_lines)
        elapsed = int(time.time() - start_time)

        if process.returncode == 0:
            logger.info(f"Session completed successfully in {elapsed}s")
            return SessionResult(success=True, output=stdout)
        else:
            logger.error(f"Session failed (exit {process.returncode}) after {elapsed}s: {stderr[:500]}")
            return SessionResult(
                success=False,
                output=stdout,
                error=stderr or f"Exit code: {process.returncode}",
            )

    except FileNotFoundError:
        error = f"Claude CLI not found at '{CLAUDE_CMD}'. Is it installed?"
        logger.error(error)
        return SessionResult(success=False, error=error)
    except Exception as e:
        error = f"Unexpected error launching session: {e}"
        logger.error(error)
        return SessionResult(success=False, error=error)


def _parse_stream_event(raw: str) -> str | None:
    """Parse a stream-json event into a human-readable log line."""
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        return raw[:300] if raw.strip() else None

    etype = event.get("type", "")

    if etype == "assistant":
        # Claude's text response
        msg = event.get("message", {})
        content = msg.get("content", [])
        parts = []
        for block in content:
            if block.get("type") == "text":
                text = block.get("text", "")
                if text.strip():
                    parts.append(text[:200])
            elif block.get("type") == "tool_use":
                tool = block.get("name", "?")
                parts.append(f"[Tool: {tool}]")
        return " ".join(parts) if parts else None

    elif etype == "content_block_start":
        block = event.get("content_block", {})
        if block.get("type") == "tool_use":
            return f"[Calling: {block.get('name', '?')}]"
        return None

    elif etype == "content_block_delta":
        delta = event.get("delta", {})
        if delta.get("type") == "text_delta":
            text = delta.get("text", "")
            return text[:200] if text.strip() else None
        elif delta.get("type") == "input_json_delta":
            return None  # Skip JSON input streaming (too noisy)
        return None

    elif etype == "result":
        return f"[Session complete — cost: ${event.get('cost_usd', '?')}, turns: {event.get('num_turns', '?')}]"

    elif etype == "system":
        return f"[System: {event.get('message', '')[:100]}]"

    return None


def _detect_phase(line: str) -> str | None:
    """Detect which agent/phase is running from Claude's output."""
    lower = line.lower()

    # Detect agent launches from Task tool usage
    phase_keywords = {
        "researcher": "researching",
        "brand-identity": "branding",
        "brand identity": "branding",
        "ux-architect": "ux_design",
        "ux architect": "ux_design",
        "copywriter": "copywriting",
        "ui-designer": "ui_design",
        "ui designer": "ui_design",
        "frontend-dev": "frontend_build",
        "frontend dev": "frontend_build",
        "create-next-app": "frontend_build",
        "seo-specialist": "seo_optimization",
        "seo specialist": "seo_optimization",
        "cx-analyst": "cx_review",
        "cx analyst": "cx_review",
        "site-validator": "validation",
        "site validator": "validation",
        "deployer": "deploying",
        "gh repo create": "github_push",
        "deploy-pages": "github_pages",
        "npm run build": "building",
        "npx create-next-app": "scaffolding",
    }

    for keyword, phase in phase_keywords.items():
        if keyword in lower:
            return phase
    return None


def build_pm_prompt(business_data: dict, theme: dict) -> str:
    """
    Build the comprehensive prompt for the Project Manager.

    This prompt is self-contained — Claude gets full instructions inline
    so it can execute every phase without needing to read agent definitions.
    """
    name = business_data.get("business_name", "Unknown")
    slug = business_data.get("slug", "site")
    industry = business_data.get("industry", "general")
    description = business_data.get("description", "")
    services = business_data.get("services", "")
    address = business_data.get("address", "")
    phone = business_data.get("phone", "")
    email = business_data.get("email", "")
    city = business_data.get("city", "")
    state = business_data.get("state", "")

    theme_name = theme.get("name", "Modern Minimal")
    theme_id = theme.get("id", "modern-minimal")
    colors = theme.get("colors", {})
    fonts = theme.get("fonts", {})
    hero_style = theme.get("hero_style", "centered")
    mood = theme.get("mood", [])

    prompt = f"""You are an elite full-stack web developer who builds Awwwards-quality websites. Your job is to build and deploy a COMPLETE multi-page marketing website that looks ultra-modern, clean, and sleek — the kind that wins design awards. You must execute ALL phases below — do NOT stop early, do NOT just plan. Actually build everything.

## Business Data
- Name: {name}
- Slug: {slug}
- Industry: {industry}
- Description: {description}
- Services: {services}
- Address: {address}
- City: {city}, {state}
- Phone: {phone}
- Email: {email}

Full data is also in brief.json in this directory.

## Theme Assignment
- Theme: {theme_name} ({theme_id})
- Primary: {colors.get('primary', '#1a1a2e')} | Secondary: {colors.get('secondary', '#16213e')} | Accent: {colors.get('accent', '#0f3460')}
- Background: {colors.get('background', '#f8f9fa')} | Text: {colors.get('text', '#212529')}
- Heading Font: {fonts.get('heading', 'Inter')} | Body Font: {fonts.get('body', 'Source Sans Pro')}
- Hero Style: {hero_style} | Mood: {', '.join(mood) if isinstance(mood, list) else mood}

## EXECUTE THESE PHASES IN ORDER

### Phase 1: Design System Generation (REQUIRED FIRST STEP)
Run the UI/UX Pro Max design system generator to get expert design recommendations:
```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "{industry} {' '.join(mood) if isinstance(mood, list) else mood}" --design-system -p "{name}"
```
Read the output carefully — it will give you: recommended pattern, style, color palette, typography, key effects, and anti-patterns to avoid.

Then get stack-specific guidelines:
```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py "layout responsive animation" --stack html-tailwind
```

Use these recommendations to inform ALL subsequent design decisions.

### Phase 2: Research (write research.json)
Use WebSearch to research the {industry} industry. Find:
- Target audience demographics and pain points
- Key selling points for this type of business
- Common competitor website features
- Industry-specific trust signals
Also search for "best {industry} website design awwwards" for design inspiration.
Write findings to research.json.

### Phase 3: Brand Identity (write brand.json)
Combine the theme colors + design system output to create brand.json with:
- Finalized color palette (primary, secondary, accent, background, text, muted)
- Typography choices (heading + body fonts with Google Fonts import URL)
- Brand voice and tone description
- Visual style: glassmorphism / gradient / minimal / etc. from design system output

### Phase 4: Site Architecture (write sitemap.json)
Design the site structure following the design system's recommended pattern:
- Home: hero, features/services, testimonials, stats bar, CTA
- About: story, team, values, timeline
- Services: individual service cards with rich descriptions
- Contact: form, map placeholder, business info
- Blog: 2-3 sample blog post outlines
Include navigation structure and CTA placement strategy.

### Phase 5: Copywriting (write content.json)
Write ALL page content — headlines, body copy, CTAs, service descriptions, about narrative, testimonials (realistic placeholder), meta descriptions. Write to content.json. Make it compelling, unique, and {industry}-appropriate.

### Phase 6: Build the Next.js Site — AWWWARDS QUALITY
This is the MAIN phase. Build a site that looks like it belongs on Awwwards.

1. Scaffold: `npx create-next-app@latest . --typescript --tailwind --app --src-dir --no-eslint --import-alias "@/*" --yes`

2. CRITICAL — Update next.config.mjs:
```js
/** @type {{import('next').NextConfig}} */
const nextConfig = {{
  output: 'export',
  images: {{ unoptimized: true }},
}};
export default nextConfig;
```

3. Update tailwind.config.ts with brand colors, fonts, custom animations, and extended theme

4. Build ALL pages and components with PREMIUM design quality:
   - src/app/layout.tsx — root layout with Google Fonts ({fonts.get('heading', 'Inter')}, {fonts.get('body', 'Source Sans Pro')}), smooth scroll
   - src/app/page.tsx — Home: stunning hero with gradient/glass effects, animated sections, services grid, testimonials, stats counter, CTA
   - src/app/about/page.tsx — About: story with timeline, values with icons, team section
   - src/app/services/page.tsx — Services: beautiful cards with hover effects, individual service detail
   - src/app/contact/page.tsx — Contact: modern form with validation, business info sidebar
   - src/app/blog/page.tsx — Blog: clean card grid with hover animations
   - Shared components: Header (floating glass navbar with blur), Footer (modern multi-column), CTAButton (with hover animation), ServiceCard (with hover lift + shadow), TestimonialCard, SectionWrapper, StatsCounter

5. DESIGN EXCELLENCE REQUIREMENTS (Awwwards-level):
   - Floating glass navbar: `backdrop-blur-xl bg-white/80 dark:bg-gray-900/80` with subtle border
   - Smooth scroll behavior: `scroll-smooth` on html
   - Section transitions: generous padding (py-20 to py-32), large gaps between sections
   - Hero: large bold typography (text-5xl to text-7xl), gradient text or accent highlights
   - Cards: subtle shadows, rounded-2xl to rounded-3xl corners, hover:shadow-xl transitions
   - Micro-animations: hover:scale-[1.02], hover:-translate-y-1, transition-all duration-300
   - Color contrast: 4.5:1 minimum ratio for accessibility
   - Touch targets: minimum 44x44px for all interactive elements
   - SVG icons only (Heroicons/Lucide style inline SVGs) — NEVER use emojis as icons
   - cursor-pointer on ALL clickable elements
   - Gradient accents: subtle gradients on backgrounds, buttons, or text
   - Whitespace: generous use of whitespace — let the design breathe
   - Typography scale: clear hierarchy with font-size jumps (base → lg → 2xl → 4xl → 6xl)
   - Container max-width: max-w-7xl mx-auto with px-4 to px-6 padding
   - Mobile-first: all layouts work perfectly at 375px, 768px, 1024px, 1440px

6. Add SEO to layout.tsx: metadata export with title, description, Open Graph, Twitter cards

7. Create public/robots.txt and public/sitemap.xml

8. Verify build succeeds: `npm run build`
   - The build MUST produce an `out/` directory (static export)
   - If build fails, fix errors and rebuild

### Phase 7: Deploy to GitHub Pages
After successful build:

1. Initialize git and push:
```bash
git init
git add .
git commit -m "Initial commit: {name} marketing site"
gh repo create marketing-{slug} --public --source=. --push --description "Marketing site for {name}"
```

2. Create .github/workflows/deploy.yml:
```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: pages
  cancel-in-progress: false
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
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
      url: ${{{{ steps.deployment.outputs.page_url }}}}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

3. Push the workflow:
```bash
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Pages deployment"
git push
```

4. Enable GitHub Pages:
```bash
gh api repos/OWNER/marketing-{slug}/pages -X POST -f build_type=workflow 2>/dev/null || true
```
(Get OWNER from: `gh api user --jq '.login'`)

### Phase 8: Write Final Report
Write status.json:
```json
{{
  "business_name": "{name}",
  "slug": "{slug}",
  "status": "complete",
  "github_url": "https://github.com/OWNER/marketing-{slug}",
  "pages_url": "https://OWNER.github.io/marketing-{slug}/",
  "phases_completed": 8
}}
```

Also write deploy-result.json with the same github_url and pages_url.

## CRITICAL RULES
- Do NOT stop after research or planning. BUILD THE ACTUAL SITE.
- Do NOT use placeholder "Lorem ipsum" text — write real content.
- The site must be UNIQUE — don't copy generic templates.
- `npm run build` MUST succeed before deploying.
- next.config.mjs MUST have `output: 'export'` and `images: {{ unoptimized: true }}`.
- Use ONLY Tailwind CSS for styling. No external UI libraries.
- All pages must be statically exportable (no API routes, no server components with dynamic data).
- Write status.json and deploy-result.json at the end with real URLs.
- NEVER use emojis as icons — use inline SVGs only (Heroicons/Lucide style).
- The site MUST look ultra-modern, clean, and sleek — Awwwards quality.
- Use glassmorphism, gradients, smooth animations, generous whitespace.
- Every hover state must have a smooth transition (150-300ms).
- Typography must have clear hierarchy with proper line-height (1.5-1.75 for body)."""

    return prompt
