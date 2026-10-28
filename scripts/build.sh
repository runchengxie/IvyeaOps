#!/usr/bin/env bash
# Build the React client into src/client/dist.
# After this, `systemctl restart ivyea-ops` (FastAPI will serve dist/).
set -e
cd "$(dirname "$0")/../src/client"
[ -d node_modules ] || npm install
npm run build
echo "Built into $(pwd)/dist"
