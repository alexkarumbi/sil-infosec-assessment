#!/usr/bin/env bash
# wait_for.sh URL [expected_status] - poll until the URL answers with the expected HTTP status (default 200).
URL=$1; WANT=${2:-200}
for i in $(seq 1 60); do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL" || true)
  [ "$CODE" = "$WANT" ] && { echo "$URL -> $CODE"; exit 0; }
  sleep 5
done
echo "Timed out waiting for $URL to return $WANT (last: $CODE)"; exit 1
