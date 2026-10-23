#!/bin/sh
set -eu

exec newman run /etc/newman/collection.json \
  --env-var "base_url=${BASE_URL}" \
  --env-var "api_key=${API_KEY}" \
  --reporters cli