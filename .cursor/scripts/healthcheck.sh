#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "==> Base environment health check"

if [[ ! -f .cursor/.install-complete ]]; then
  echo "ERROR: install marker missing; run install first" >&2
  exit 1
fi

echo "Install marker: $(cat .cursor/.install-complete)"
echo "Git: $(git --version)"
echo "Python: $(python3 --version)"
echo "Repository: $(basename "$REPO_ROOT")"

if curl -sf http://127.0.0.1:8080/ >/dev/null 2>&1; then
  echo "Docs server: responding on http://127.0.0.1:8080/"
else
  echo "Docs server: not running (start the docs terminal to serve public/)"
fi

echo "==> Health check passed"
