#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DOMAIN:-}" ]]; then
  echo "DOMAIN is not set. Export DOMAIN before running."
  exit 1
fi

echo "Checking app health..."
curl -sf "https://${DOMAIN}/api/health" | python3 -m json.tool

echo "Checking admin route..."
status="$(curl -s -o /dev/null -w "%{http_code}" "https://${DOMAIN}/admin")"
if [[ "${status}" != "200" ]]; then
  echo "Admin route failed with status ${status}"
  exit 1
fi
echo "Admin route OK"
