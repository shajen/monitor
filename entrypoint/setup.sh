#!/bin/bash

export DJANGO_SUPERUSER_PASSWORD=${HTTP_PASSWORD:-password} 

python3 manage.py migrate
python3 manage.py createsuperuser --noinput --username ${HTTP_USER:-admin} --email admin@local.local &> /dev/null || true