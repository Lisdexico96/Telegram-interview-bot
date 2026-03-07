#!/bin/sh
# Run the Python bot using whatever Python 3 is available
if command -v python3 >/dev/null 2>&1; then
  exec python3 bot.py "$@"
elif command -v python >/dev/null 2>&1; then
  exec python bot.py "$@"
else
  echo "Error: neither python3 nor python found in PATH" >&2
  exit 1
fi
