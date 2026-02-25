#!/bin/sh
set -e
export DOMAIN="${DOMAIN:-stocksense.thatinsaneguy.com}"
envsubst '${DOMAIN}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf
exec nginx -g 'daemon off;'
