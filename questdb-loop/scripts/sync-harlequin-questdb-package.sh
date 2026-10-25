#!/usr/bin/env bash
# Copy canonical adapter source and loop docs into the PyPI staging tree.
# Rewrites ADAPTER_DETAILS doc paths only in the staged adapter.py.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
STAGING="${REPO_ROOT}/questdb-loop/package/harlequin-questdb"
SRC_ADAPTER="${REPO_ROOT}/src/harlequin_questdb"
STAGED_ADAPTER="${STAGING}/src/harlequin_questdb"

mkdir -p "${STAGED_ADAPTER}" "${STAGING}/docs"

rsync -a --delete "${SRC_ADAPTER}/" "${STAGED_ADAPTER}/"
rsync -a "${REPO_ROOT}/questdb-loop/docs/"*.md "${STAGING}/docs/"
cp "${REPO_ROOT}/questdb-loop/docker-compose.yml" "${STAGING}/docker-compose.yml"

STAGED_ADAPTER_PY="${STAGED_ADAPTER}/adapter.py"
STAGED_USER_GUIDE="${STAGING}/docs/USER_GUIDE.md"
sed -i \
  -e 's|questdb-loop/docs/KNOWN_LIMITATIONS.md|docs/KNOWN_LIMITATIONS.md|g' \
  -e 's|questdb-loop/docs/USER_GUIDE.md|docs/USER_GUIDE.md|g' \
  "${STAGED_ADAPTER_PY}"
sed -i \
  -e 's|questdb-loop/docker-compose.yml|docker-compose.yml|g' \
  "${STAGED_USER_GUIDE}"
