#!/usr/bin/env bash
# Bootstrap FossilScanner for development on Termux or Linux.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "FossilScanner bootstrap"
echo "Root: $ROOT"

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 not found. Install it and re-run."
    exit 1
fi

echo "Checking Python version..."
python3 - <<'PY'
import sys
if sys.version_info < (3, 9):
    print("Python 3.9 or later required.")
    sys.exit(1)
print("OK:", sys.version.split()[0])
PY

echo "Installing dev dependencies (optional)..."
python3 -m pip install --quiet --upgrade pip || true
python3 -m pip install --quiet pytest || true

echo "Running Python syntax check..."
python3 -m compileall -q src

echo "Running tests..."
PYTHONPATH="$ROOT/src" python3 -m pytest -q tests || echo "Some tests failed; see output."

echo "Bootstrap complete."
echo "To run the CLI:"
echo "  export PYTHONPATH=$ROOT/src"
echo "  python3 -m fossil_scanner.cli preflight --work-dir ~/fieldwork"
