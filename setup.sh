#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check() {
  if command -v "$1" &>/dev/null; then
    echo -e "${GREEN}[OK]${NC} $1 found: $(command -v "$1")"
    return 0
  else
    echo -e "${RED}[MISSING]${NC} $1 not found"
    return 1
  fi
}

echo "=== Marketing Site Factory — Setup ==="
echo ""

# Check prerequisites
echo "--- Checking prerequisites ---"
MISSING=0
check node || MISSING=1
check npm || MISSING=1
check python3 || MISSING=1
check pip3 || MISSING=1
check gh || MISSING=1
check claude || MISSING=1

if [ "$MISSING" -eq 1 ]; then
  echo ""
  echo -e "${YELLOW}Install missing tools before continuing:${NC}"
  echo "  node/npm:  https://nodejs.org/"
  echo "  python3:   https://python.org/"
  echo "  gh:        brew install gh && gh auth login"
  echo "  claude:    https://claude.ai/code"
  exit 1
fi

# Check auth status
echo ""
echo "--- Checking authentication ---"

if gh auth status &>/dev/null 2>&1; then
  echo -e "${GREEN}[OK]${NC} GitHub CLI authenticated"
else
  echo -e "${YELLOW}[WARN]${NC} GitHub CLI not authenticated. Run: gh auth login"
fi

if [ -n "${GITHUB_TOKEN:-}" ]; then
  echo -e "${GREEN}[OK]${NC} GITHUB_TOKEN is set"
else
  echo -e "${YELLOW}[WARN]${NC} GITHUB_TOKEN not set. Set it with: export GITHUB_TOKEN=your_token"
fi

# Check Claude Code CLI is authenticated
if claude --version &>/dev/null 2>&1; then
  echo -e "${GREEN}[OK]${NC} Claude Code CLI available"
else
  echo -e "${YELLOW}[WARN]${NC} Claude Code CLI not responding. Ensure you are logged in."
fi

# Create directories
echo ""
echo "--- Creating directories ---"
for dir in workspace data logs; do
  mkdir -p "$dir"
  echo -e "${GREEN}[OK]${NC} $dir/"
done

# Install Python deps
echo ""
echo "--- Installing Python dependencies ---"
pip3 install -r requirements.txt

# Write local settings template if not exists
if [ ! -f .claude/settings.local.json ]; then
  cat > .claude/settings.local.json << 'EOF'
{
  "env": {
    "GITHUB_TOKEN": ""
  }
}
EOF
  echo -e "${YELLOW}[ACTION]${NC} Fill in tokens in .claude/settings.local.json"
else
  echo -e "${GREEN}[OK]${NC} .claude/settings.local.json already exists"
fi

# Place gitkeep files
touch workspace/.gitkeep data/.gitkeep logs/.gitkeep

echo ""
echo -e "${GREEN}=== Setup complete ===${NC}"
echo "Next steps:"
echo "  1. Place your spreadsheet in data/"
echo "  2. Export token: export GITHUB_TOKEN=your_token"
echo "  3. Start dashboard: python -m dashboard.app   (open http://localhost:3000)"
echo "  4. Or CLI: python -m orchestrator.main --spreadsheet data/YOUR_FILE.csv --count 1 --dry-run"
