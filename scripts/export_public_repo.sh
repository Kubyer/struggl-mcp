#!/usr/bin/env bash
# Safely export `packages/struggl-mcp` into an isolated standalone Git repository
# with ZERO private monorepo commit history and mandatory secret verification.
#
# Usage:
#   ./packages/struggl-mcp/scripts/export_public_repo.sh /tmp/struggl-mcp-public

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${1:-}"

if [[ -z "${TARGET_DIR}" ]]; then
  echo "Usage: $0 <target-export-directory>" >&2
  exit 1
fi

if [[ -e "${TARGET_DIR}" ]]; then
  echo "Error: target directory '${TARGET_DIR}' already exists. Choose a fresh directory." >&2
  exit 1
fi

# 1. Run strict zero-secret & manifest verification BEFORE copying
python3 "${SCRIPT_DIR}/verify_public_bundle.py" "${BUNDLE_DIR}"

# 2. Copy clean bundle without any parent .git metadata or Python caches
mkdir -p "${TARGET_DIR}"
rsync -a \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='dist' \
  --exclude='build' \
  --exclude='*.egg-info' \
  --exclude='node_modules' \
  --exclude='*.tgz' \
  --exclude='.pytest_cache' \
  --exclude='.ruff_cache' \
  --exclude='.DS_Store' \
  "${BUNDLE_DIR}/" "${TARGET_DIR}/"

# 3. Re-verify the exported target directory
python3 "${TARGET_DIR}/scripts/verify_public_bundle.py" "${TARGET_DIR}"

# 4. Initialize a brand-new orphan Git repository (1 commit, zero parent history)
(
  cd "${TARGET_DIR}"
  git init -b main >/dev/null
  if [[ -z "$(git config user.name || true)" ]]; then
    git config user.name "STRUGGL"
  fi
  if [[ -z "$(git config user.email || true)" ]]; then
    git config user.email "noreply@singandclap.com"
  fi
  git add .
  git commit -m "Initial public release of struggl-mcp (MCP server + struggl-coach Agent Skill)" >/dev/null
)

echo "Exported clean single-commit public repo to: ${TARGET_DIR}"
echo "Next steps when ready to publish:"
echo "  cd ${TARGET_DIR}"
echo "  git remote add origin git@github.com:Kubyer/struggl-mcp.git"
echo "  git push -u origin main"
