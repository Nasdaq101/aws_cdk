#!/bin/bash
# Demo Steps 1-2: (Optional) reset repo to a commit, then deploy all CDK stacks.
#
# Usage:
#   ./demo_2_deploy.sh                  # deploy without resetting git
#   ./demo_2_deploy.sh <commit-hash>    # git reset --hard then deploy
#
# Prerequisites:
#   - Docker running  (needed to build the matplotlib Lambda Layer)
#   - AWS credentials configured
#   - Node.js + AWS CDK CLI: npm install -g aws-cdk
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CDK_DIR="$SCRIPT_DIR/cdk"

# ── Optional git reset ────────────────────────────────────────────────────────
if [ -n "$1" ]; then
  echo "[Git] Resetting to $1"
  git -C "$SCRIPT_DIR" reset --hard "$1"
  echo "[Git] HEAD is $(git -C "$SCRIPT_DIR" rev-parse --short HEAD)"
fi

# ── CDK Python dependencies (use venv to avoid PEP 668 error) ────────────────
VENV_DIR="$CDK_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "[1/3] Creating virtual environment & installing CDK Python dependencies..."
  python3 -m venv "$VENV_DIR"
else
  echo "[1/3] Installing CDK Python dependencies..."
fi
source "$VENV_DIR/bin/activate"
pip install -q -r "$CDK_DIR/requirements.txt"

echo "[2/3] CDK bootstrap..."
cd "$CDK_DIR"
cdk bootstrap

echo "[3/3] Deploying stacks (matplotlib layer may take ~2 min first time)..."
cdk deploy --all --require-approval never

echo ""
echo "Deployment complete. Stacks: StorageStack, LambdaStack, ApiStack."
echo "Next: ./demo_5_invoke.sh"
