#!/usr/bin/env bash
set -euo pipefail

FRAPPE_DOCKER_ROOT="${1:-$PWD}"
IMAGE_TAG="${IMAGE_TAG:-golden-erpnext:16-estateflow-0.1.5}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPS_JSON="${SCRIPT_DIR}/apps.json"

if [[ ! -f "${FRAPPE_DOCKER_ROOT}/images/layered/Containerfile" ]]; then
  echo "Frappe Docker layered Containerfile not found in: ${FRAPPE_DOCKER_ROOT}" >&2
  echo "Usage: $0 /absolute/path/to/frappe_docker" >&2
  exit 1
fi

python3 -m json.tool "${APPS_JSON}" >/dev/null

echo "Building ${IMAGE_TAG} with apps from ${APPS_JSON}"
docker build \
  --no-cache \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --secret=id=apps_json,src="${APPS_JSON}" \
  --tag="${IMAGE_TAG}" \
  --file="${FRAPPE_DOCKER_ROOT}/images/layered/Containerfile" \
  "${FRAPPE_DOCKER_ROOT}"

echo "Built ${IMAGE_TAG}"
