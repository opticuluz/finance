#!/bin/bash

set -e

envsubst '$APP_HOST $APP_PORT' < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf

echo "Checking NGINX config..."
nginx -t

echo "Starting nginx..."

nginx -g 'daemon off;'
