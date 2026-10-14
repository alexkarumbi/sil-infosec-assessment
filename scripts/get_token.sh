#!/usr/bin/env bash
# get_token.sh [username] - print an access token for a lab user (password from LAB_USER_PASSWORD or lab/.env).
# Uses the password grant: acceptable for a lab/CI demo only. Production uses Authorization Code + PKCE.
set -euo pipefail
USER_NAME=${1:-dr.wanjiru}
if [ -z "${LAB_USER_PASSWORD:-}" ]; then
  LAB_USER_PASSWORD=$(grep '^LAB_USER_PASSWORD=' "$(dirname "$0")/../lab/.env" | cut -d= -f2-)
fi
curl -sf -X POST "${KC_URL:-http://localhost:8081}/realms/sil/protocol/openid-connect/token" \
  -d grant_type=password -d client_id=sil-portal \
  --data-urlencode "username=$USER_NAME" --data-urlencode "password=$LAB_USER_PASSWORD" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
