#!/bin/bash
# Runs the Oracle XE container where the submissions are executed, in the foreground (systemd
# keeps track of it). Used by deploy/oracle-xe.service.example, which reads <base>/env as its
# EnvironmentFile:
#   ORACLE_PASS  password of SYSTEM (the same one the judge uses). It is passed to the container
#                through the environment, not in the command line, so it does not show in "ps".
#                Only letters, digits, "_" and "-": the image fails with others such as "&"
#   ORACLE_PORT  local port where Oracle is published (127.0.0.1 only)
# Optional: ORACLE_CONTAINER (container name, lsql-oracle by default) and ORACLE_IMAGE.
# The container has no volume: Oracle only holds the temporary users of the submissions, so a
# fresh database on every start is fine.
set -euo pipefail
: "${ORACLE_PASS:?ORACLE_PASS is not defined}"
: "${ORACLE_PORT:?ORACLE_PORT is not defined}"
export ORACLE_PASSWORD="$ORACLE_PASS"
exec /usr/bin/docker run --rm --name "${ORACLE_CONTAINER:-lsql-oracle}" --shm-size=2g \
    -p "127.0.0.1:$ORACLE_PORT:1521" -e ORACLE_PASSWORD "${ORACLE_IMAGE:-gvenzl/oracle-xe:21-slim}"
