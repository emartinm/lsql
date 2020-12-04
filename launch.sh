#!/usr/bin/env bash

# From https://stackoverflow.com/questions/19331497/set-environment-variables-from-file-of-key-value-pairs
export $(grep -v '^#' .env | xargs -d '\n')
echo -e '\e[1;32m[Loaded environment from .env file]\e[0m'

source venv/bin/activate

cd lsql

python manage.py runserver
