#!/bin/bash
# Restores a backup made by backup.sh. It REPLACES the whole database of the judge with the
# one in the backup (it first makes a backup of the current one, if it has data). Run it as root:
#   sudo <base>/app/deploy/restore.sh <backup.tar>
#   sudo <base>/app/deploy/restore.sh <backup.tar> --yes     # without asking for confirmation
# If <base>/env does not exist (a new server), it is restored from the backup; if it exists,
# the current one is kept. The database and its user must already exist (DEPLOYMENT.md, step 3,
# with the PG_PASS of <base>/env). After loading the dump it applies the migrations of the
# current code and, if the service is installed, restarts it and checks the login page.
# See common.sh for the variables.
set -euo pipefail
. "$(dirname "$0")/common.sh"

BACKUP=${1:-}
YES=${2:-}
[ -n "$BACKUP" ] || fail "uso: $0 <copia.tar> [--yes]"
[ -f "$BACKUP" ] || fail "no existe $BACKUP"
require_root
require_install noenv

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
tar -C "$TMP" --no-same-owner -xf "$BACKUP"
DIR=$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -n 1)
for f in db.dump env info.txt; do
    [ -f "$DIR/$f" ] || fail "$BACKUP no es una copia de backup.sh (falta $f)"
done

step "Copia"
cat "$DIR/info.txt"
CURRENT=$(as_owner git -C "$APP" rev-parse HEAD)
grep -q "^commit: $CURRENT$" "$DIR/info.txt" ||
    echo "AVISO: el código instalado es otro commit ($(as_owner git -C "$APP" log -1 --format='%h %s'));" \
        "si es más reciente, migrate actualizará la base de datos."

if [ ! -f "$BASE/env" ]; then
    step "Configuración"
    install -o "$OWNER" -m 600 "$DIR/env" "$BASE/env"
    echo "$BASE/env restaurado desde la copia."
elif ! cmp -s "$DIR/env" "$BASE/env"; then
    echo "AVISO: $BASE/env es distinto del de la copia; se mantiene el actual" \
        "(el de la copia: tar -xOf $BACKUP $(basename "$DIR")/env)."
fi

DB=$(env_value PG_DB)
TABLES=$(pg psql -tA -c "SELECT count(*) FROM pg_tables WHERE schemaname = 'public'" </dev/null) ||
    fail "no se puede conectar a la base de datos $DB: crea su usuario y la base de datos con
la contraseña PG_PASS de $BASE/env (DEPLOYMENT.md, paso 3 del despliegue)."

if [ "$YES" != "--yes" ]; then
    echo
    read -r -p "Se borrarán todos los datos de la base de datos $DB. Escribe «restaurar» para continuar: " answer ||
        answer=""
    [ "$answer" = restaurar ] || fail "cancelado"
fi

if [ "$TABLES" -gt 0 ]; then
    step "Copia de seguridad del estado actual"
    "$APP/deploy/backup.sh"
fi

if systemctl cat "$SERVICE" >/dev/null 2>&1; then
    step "Parando $SERVICE"
    systemctl stop "$SERVICE"
    INSTALLED=1
fi

step "Restaurando la base de datos $DB"
# The schema is created again, so no table of a newer version of the judge is left behind
pg psql -q -v ON_ERROR_STOP=1 -c "SET client_min_messages = warning" -c "DROP SCHEMA public CASCADE" \
    -c "CREATE SCHEMA public" </dev/null
pg pg_restore --no-owner --no-privileges --exit-on-error --single-transaction <"$DIR/db.dump" ||
    fail "no se ha podido restaurar: la base de datos ha quedado vacía (la copia del estado anterior
está en ${BACKUP_DIR:-$BASE/backups})."

step "Migraciones"
manage migrate --noinput

if [ -n "${INSTALLED:-}" ]; then
    restart_and_check
else
    echo
    echo "OK: base de datos restaurada. El servicio $SERVICE no está instalado: continúa con el despliegue."
fi
