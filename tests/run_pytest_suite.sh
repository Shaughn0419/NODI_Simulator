#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -d "${ROOT_DIR}/.pytest_vendor" ]]; then
  echo "Missing ${ROOT_DIR}/.pytest_vendor. Install pytest and pytest-xdist first." >&2
  exit 1
fi

cd "${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}/.pytest_vendor${PYTHONPATH:+:${PYTHONPATH}}"

python -m pytest tests -m "not app_interactions" -n 8 -q
python -m pytest tests -m "app_interactions" -q
