#!/usr/bin/env bash
# PreToolUse hook: Ensures Write/Edit operations stay within the current workspace.
# Reads tool input from stdin (JSON), checks that file_path is under $PWD.
# Exit 0 = allow, Exit 2 = block.

set -euo pipefail

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
inp = data.get('tool_input', {})
print(inp.get('file_path', inp.get('path', '')))
" 2>/dev/null || echo "")

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Resolve to absolute path
RESOLVED=$(python3 -c "
import os, sys
p = sys.argv[1]
cwd = sys.argv[2]
if not os.path.isabs(p):
    p = os.path.join(cwd, p)
print(os.path.realpath(p))
" "$FILE_PATH" "$PWD" 2>/dev/null || echo "$FILE_PATH")

WORKSPACE_DIR=$(python3 -c "import os; print(os.path.realpath('$PWD'))" 2>/dev/null || echo "$PWD")

if [[ "$RESOLVED" == "$WORKSPACE_DIR"* ]]; then
  exit 0
else
  echo '{"decision": "block", "reason": "File write blocked: path '"$RESOLVED"' is outside workspace '"$WORKSPACE_DIR"'"}'  >&2
  exit 2
fi