#!/usr/bin/env bash
# Refuse an automatic restart of a service still pointing to the old source path.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if command -v systemctl >/dev/null 2>&1; then
  current="$(systemctl show ivyea-ops.service -p WorkingDirectory --value 2>/dev/null || true)"
  if [ "$current" = "$repo_root/server" ]; then
    echo 'The installed systemd unit still uses the old server/ source path.' >&2
    echo 'Automatic update/restart stopped. Follow docs/repository-layout.md to migrate WorkingDirectory, PYTHONPATH and ExecStart, then daemon-reload.' >&2
    exit 2
  fi
fi
