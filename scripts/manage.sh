#!/usr/bin/env bash
# Native Unix entry point. A foreground server stops with Ctrl+C.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
action="${1:-start}"
if [ "$#" -gt 0 ]; then shift; fi
case "$action" in
  install) entry=install.sh ;;
  start) entry=start.sh ;;
  update) entry=update.sh ;;
  *) echo 'Usage: bash scripts/manage.sh {install|start|update} [--dry-run]' >&2; exit 2 ;;
esac
if [ "${1:-}" = '--dry-run' ]; then printf 'bash %q\n' "$script_dir/$entry"; exit 0; fi
exec bash "$script_dir/$entry" "$@"
