# Shared by update.sh, backup.sh and restore.sh (sourced, not executed). Layout of manage.sh:
# <base>/app, <base>/venv, <base>/env. JUDGE_BASE sets <base> when the scripts are run from
# another place; SERVICE overrides the name of the systemd service (lsql by default);
# PG_IMAGE is the Docker image with pg_dump/pg_restore, of the same major version as the server.

BASE=${JUDGE_BASE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}
APP="$BASE/app"
SERVICE=${SERVICE:-lsql}
PG_IMAGE=${PG_IMAGE:-postgres:16}

step() { printf '\n==> %s\n' "$*"; }
fail() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

require_root() { [ "$(id -u)" -eq 0 ] || fail "ejecútalo con sudo"; }

# Checks that <base>/app exists (and <base>/env, with "env") and sets OWNER
require_install() {
    if [ ! -d "$APP/.git" ] || { [ "$1" = env ] && [ ! -f "$BASE/env" ]; }; then
        fail "no hay un juez instalado en $BASE (falta $APP o $BASE/env).
Ejecuta el script desde <base>/app/deploy/ o indica la instalación: sudo JUDGE_BASE=<base> $0"
    fi
    OWNER=$(stat -c %U "$APP")
}

as_owner() { sudo -u "$OWNER" "$@"; }
manage() { as_owner "$APP/deploy/manage.sh" "$@"; }
env_value() { sed -n "s/^$1=//p" "$BASE/env" | tail -n 1; }

# Runs a PostgreSQL client in a temporary container, connected to the database of the judge
# with its own user (the password goes in the environment, not in the command line). It reads
# the standard input: redirect it (</dev/null) when the client does not need it.
pg() {
    local tool=$1
    shift
    PGPASSWORD=$(env_value PG_PASS) docker run --rm -i --network host -e PGPASSWORD "$PG_IMAGE" \
        "$tool" -h "$(env_value PG_SERVER)" -p "$(env_value PG_PORT)" -U "$(env_value PG_USER)" \
        -d "$(env_value PG_DB)" "$@"
}

# Restarts (or starts) the service and checks that the login page answers through gunicorn
restart_and_check() {
    step "Reiniciando $SERVICE"
    systemctl restart "$SERVICE"
    for _ in $(seq 1 20); do
        systemctl is-active --quiet "$SERVICE" && break
        sleep 1
    done
    systemctl is-active --quiet "$SERVICE" || {
        journalctl -u "$SERVICE" -n 30 --no-pager
        fail "$SERVICE no ha arrancado"
    }

    step "Comprobando la página de entrada"
    local host bind code=""
    host=$(env_value ALLOWED_HOSTS | cut -d, -f1)
    bind=$(env_value GUNICORN_BIND)
    # Directly to gunicorn: without the header that nginx adds, the judge redirects to HTTPS
    for _ in $(seq 1 20); do
        code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: $host" -H "X-Forwarded-Proto: https" \
            "http://$bind/sql/login/" || true)
        [ "$code" = 200 ] && break
        sleep 1
    done
    [ "$code" = 200 ] || {
        journalctl -u "$SERVICE" -n 30 --no-pager
        fail "la página de entrada responde $code"
    }
    echo "OK: https://$host/sql/ responde (versión $(as_owner git -C "$APP" log -1 --format='%h %s'))"
}
