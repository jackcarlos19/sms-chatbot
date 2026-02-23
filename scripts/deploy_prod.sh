#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ ! -f ".env" ]]; then
  echo "Missing .env file in ${ROOT_DIR}"
  exit 1
fi

if [[ -z "${DOMAIN:-}" ]]; then
  echo "DOMAIN is not set in environment. Export DOMAIN before running."
  exit 1
fi

echo "Pulling latest changes..."
git pull --ff-only

echo "Rebuilding and starting production stack..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "Running database migrations..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T app alembic upgrade head

echo "Health check..."
curl -sf "https://${DOMAIN}/api/health" | python3 -m json.tool

echo "Deployment complete."
