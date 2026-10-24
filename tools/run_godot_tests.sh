#!/usr/bin/env bash
# Full runtime gate for Aeryvex Pro, Godot 3.5/3.6.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GODOT="${GODOT_BIN:-}"
if [[ -z "$GODOT" ]]; then
  for name in godot3 godot3.6 godot; do
    if command -v "$name" >/dev/null 2>&1; then GODOT="$(command -v "$name")"; break; fi
  done
fi
if [[ -z "$GODOT" ]]; then
  echo 'FAIL: Godot 3.5/3.6 not found. Set GODOT_BIN=/path/to/Godot3.' >&2; exit 2
fi
VERSION="$($GODOT --version 2>&1)"
echo "Godot: $VERSION ($GODOT)"
if [[ "$VERSION" != 3.* ]]; then echo 'FAIL: project requires Godot 3.x' >&2; exit 2; fi
LOG_DIR="$ROOT/test_logs"
mkdir -p "$LOG_DIR"
FAILED=0
# Include all runtime tests previously omitted from the launcher.
for test in runtime_smoke runtime_combat runtime_animation runtime_ai runtime_skinning runtime_duel runtime_fronts; do
  echo "===== $test ====="
  LOG="$LOG_DIR/${test}.log"
  if "$GODOT" --no-window --path "$ROOT" -s "res://tests/$test.gd" >"$LOG" 2>&1; then
    cat "$LOG"
    if grep -Eiq 'SCRIPT ERROR|Parse Error|Invalid call|Invalid get index|FATAL ERROR' "$LOG"; then
      echo "FAILED: Godot reported engine errors in $test"; FAILED=1
    else
      echo "PASSED: $test"
    fi
  else
    cat "$LOG"
    echo "FAILED: $test"
    FAILED=1
  fi
done
if [[ "$FAILED" -ne 0 ]]; then
  echo "RUNTIME TESTS FAILED — inspect $LOG_DIR"; exit 1
fi
echo 'ALL SEVEN GODOT RUNTIME TESTS PASSED'
