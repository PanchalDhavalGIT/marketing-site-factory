#!/usr/bin/env bash
# PostToolUse hook: Logs Bash command executions per-site for audit trail.

set -euo pipefail

INPUT=$(cat)

SITE_SLUG=$(basename "$PWD")
LOG_DIR="logs"
LOG_FILE="${LOG_DIR}/${SITE_SLUG}.log"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

mkdir -p "$LOG_DIR"

python3 -c "
import sys, json

data = json.load(sys.stdin)
tool = data.get('tool_name', 'unknown')
inp = data.get('tool_input', {})
cmd = inp.get('command', '')

entry = {
    'timestamp': '$TIMESTAMP',
    'tool': tool,
    'command': cmd[:500]
}

with open('$LOG_FILE', 'a') as f:
    f.write(json.dumps(entry) + '\n')
" <<< "$INPUT" 2>/dev/null || true

exit 0