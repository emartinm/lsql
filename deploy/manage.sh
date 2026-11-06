#!/bin/bash
# Runs manage.py in production with the configuration of the deployment. Expected layout:
#   <base>/app   this repository
#   <base>/venv  virtualenv
#   <base>/env   configuration (deploy/env.example), readable only by the user of the judge
# Example: sudo -u <user> <base>/app/deploy/manage.sh migrate
BASE=$(cd "$(dirname "$0")/../.." && pwd)
# The env file is read literally, as systemd does with EnvironmentFile (it is not sourced): values
# such as a SECRET_KEY with '#', '$' or '&' are kept as they are
while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in '' | '#'* | ';'*) continue ;; esac
    export "${line%%=*}=${line#*=}"
done <"$BASE/env"
cd "$BASE/app/lsql" && exec "$BASE/venv/bin/python" manage.py "$@"
