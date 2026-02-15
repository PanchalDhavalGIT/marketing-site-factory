#!/usr/bin/env bash
# Stop hook: Saves session completion status to progress tracker.
# Called when a Claude Code session ends.

set -euo pipefail

INPUT=$(cat)

SESSION_ID=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('session_id', 'unknown'))
" 2>/dev/null || echo "unknown")

PROGRESS_FILE="logs/progress.json"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Extract site slug from workspace directory name
SITE_SLUG=$(basename "$PWD")

if [ -f "$PROGRESS_FILE" ]; then
  python3 -c "
import json, sys

slug = '$SITE_SLUG'
ts = '$TIMESTAMP'
sid = '$SESSION_ID'

with open('$PROGRESS_FILE', 'r') as f:
    progress = json.load(f)

if slug in progress:
    progress[slug]['last_session_id'] = sid
    progress[slug]['last_updated'] = ts
    if progress[slug]['status'] not in ('complete', 'failed'):
        progress[slug]['status'] = 'session_ended'

with open('$PROGRESS_FILE', 'w') as f:
    json.dump(progress, f, indent=2)
" 2>/dev/null || true
fi

exit 0