#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "==> Base environment install"

required_tools=(git curl python3)
for tool in "${required_tools[@]}"; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "ERROR: missing required tool: $tool" >&2
    exit 1
  fi
done

if [[ ! -f README.md ]]; then
  echo "ERROR: repository checkout is incomplete (README.md missing)" >&2
  exit 1
fi

pip3 install -q -r "$REPO_ROOT/requirements.txt"

mkdir -p .cursor public data
date -u +"%Y-%m-%dT%H:%M:%SZ" > .cursor/.install-complete

echo "==> Install complete ($(cat .cursor/.install-complete))"
