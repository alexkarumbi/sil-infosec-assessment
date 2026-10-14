#!/usr/bin/env bash
# Start the lab in the right order: Keycloak + DB first, render Kong's config with the realm key, then the rest.
# Usage: scripts/lab_up.sh                 (everything)
#        scripts/lab_up.sh waf kong ...    (only the named services, e.g. in CI)
set -euo pipefail
cd "$(dirname "$0")/../lab"

[ -f .env ] || { echo "lab/.env missing: cp .env.example .env and set the passwords"; exit 1; }
mkdir -p logs/{waf,kong,ai,squid}
chmod -R 777 logs            # lab shortcut so non-root containers can write their logs

docker compose up -d keycloak db
python3 ../scripts/render_kong_config.py http://localhost:8081

if [ "$#" -gt 0 ]; then
  docker compose up -d --build "$@"
else
  docker compose up -d --build
fi

../scripts/wait_for.sh http://localhost:8080/api/v1/patients 401
echo "Lab is up: WAF http://localhost:8080 | Keycloak http://localhost:8081"
