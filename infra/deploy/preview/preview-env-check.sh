#!/bin/sh
set -eu

require_value() {
  name="$1"
  eval "value=\${$name:-}"
  if [ -z "$value" ]; then
    echo "PetAccess Preview deployment missing required variable: $name" >&2
    exit 64
  fi
  case "$value" in
    *CHANGE_ME*|*change_me*|*example.com*|*example.invalid*)
      echo "PetAccess Preview deployment refuses placeholder value for $name" >&2
      exit 64
      ;;
  esac
}

require_value PETACCESS_PREVIEW_DOMAIN
require_value DATABASE_URL
require_value POSTGRES_PASSWORD
require_value S3_ACCESS_KEY
require_value S3_SECRET_KEY
require_value JWT_SECRET

case "\${APP_ENV:-}" in
  staging) ;;
  *)
    echo "PetAccess public Preview must run with APP_ENV=staging" >&2
    exit 64
    ;;
esac

case "\${API_BASE_URL:-}" in
  "https://\${PETACCESS_PREVIEW_DOMAIN}/api/v1") ;;
  *)
    echo "API_BASE_URL must equal https://\${PETACCESS_PREVIEW_DOMAIN}/api/v1" >&2
    exit 64
    ;;
esac

if [ "\${FEATURE_REAL_MAP:-false}" = "true" ]; then
  require_value TENCENT_MAP_KEY_CLIENT
  require_value TENCENT_MAP_KEY_SERVER
fi

echo "PetAccess Preview deployment environment: OK" >&2
