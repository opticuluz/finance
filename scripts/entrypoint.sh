#!/bin/sh

set -e

python manage.py collectstatic --noinput

python manage.py wait_for_db

python manage.py migrate

uwsgi --socket :9000 --workers 4 --master --enable-threads --module finance.wsgi --http-timeout 86400 --http-keepalive
