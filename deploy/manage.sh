#!/bin/bash
# Runs manage.py in production with the configuration of the deployment. Expected layout:
#   <base>/app   this repository
#   <base>/venv  virtualenv
#   <base>/env   configuration (deploy/env.example), readable only by the user of the judge
# Example: sudo -u <user> <base>/app/deploy/manage.sh migrate
BASE=$(cd "$(dirname "$0")/../.." && pwd)
set -a
. "$BASE/env"
set +a
cd "$BASE/app/lsql" && exec "$BASE/venv/bin/python" manage.py "$@"
