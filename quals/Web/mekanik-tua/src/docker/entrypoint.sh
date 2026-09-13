#!/bin/sh
set -e

if [ -z "$GZCTF_FLAG" ]; then
    echo "GZCTF_FLAG is not set" >&2
    exit 1
fi

APP_PEPPER=$(php -r 'echo bin2hex(random_bytes(32));')
SESSION_SECRET=$(php -r 'echo bin2hex(random_bytes(16));')
export APP_PEPPER SESSION_SECRET

rm -f "$DB_PATH"
php /app/backend/bin/seed.php
chown -R www-data:www-data "$(dirname "$DB_PATH")"

exec supervisord -c /etc/supervisord.conf
