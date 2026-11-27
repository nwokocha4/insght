#!/bin/sh
# Smoke: stage the reference extractor as /app/solve.py and run it against the
# staged paper. From a repo checkout, stage the data under a temp dir instead.
set -e
REF="$(cd "$(dirname "$0")" && pwd)/solve.py"
if [ -d /app/data ]; then
 cp "$REF" /app/solve.py
 python3 /app/solve.py
 ls /app/output
else
 STAGE="${CAMTRAP_SMOKE_DIR:-/tmp/camtrap_extract_smoke}"
 rm -rf "$STAGE"
 mkdir -p "$STAGE/output"
 cp -r "$(cd "$(dirname "$0")/../environment" && pwd)/data" "$STAGE/data"
 CAMTRAP_BASE="$STAGE" python3 "$REF"
 ls "$STAGE/output"
fi
