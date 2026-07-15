#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8080}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-frappe_docker-backend-1}"
SITE_NAME="${SITE_NAME:-mysite.localhost}"

check_asset() {
  local path="$1"
  local result
  result="$(curl -sS -o /dev/null -w '%{http_code} %{content_type}' "${BASE_URL}${path}")"
  printf '%-62s %s\n' "$path" "$result"
  [[ "$result" == 200\ text/css* ]]
}

check_asset "/assets/estateflow/css/estateflow.css?v=0.1.4"
check_asset "/assets/estateflow/css/estateflow-guide.css?v=0.1.4"

docker exec "${BACKEND_CONTAINER}" bash -lc "
cd /home/frappe/frappe-bench &&
bench --site '${SITE_NAME}' list-apps &&
bench --site '${SITE_NAME}' execute \"frappe.db.count('DocType', {'module': 'EstateFlow'})\"
"

docker ps --format 'table {{.Names}}\t{{.Status}}' | grep 'frappe_docker-'
