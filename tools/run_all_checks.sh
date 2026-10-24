#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
python3 -m compileall -q tests
for test in tests/check_*.py; do
  echo "===== $test ====="
  python3 "$test"
done
bash tools/run_godot_tests.sh
