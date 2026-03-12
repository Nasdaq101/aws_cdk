#!/bin/bash
# Demo Step 0: Destroy all CDK stacks/resources.
# make sure the demo is started from a clean state.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CDK_DIR="$SCRIPT_DIR/cdk"

echo "Destroying all CDK stacks..."
cd "$CDK_DIR"
# Use venv so the same Python that runs app.py has aws_cdk installed
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt
cdk destroy --all --force
echo "Done."
