#!/bin/bash
# Updates the judge in production to the latest version of the repository. Run it as root:
#   sudo <base>/app/deploy/update.sh            # only if there are new commits
#   sudo <base>/app/deploy/update.sh --force    # even if there are none
# Steps: git pull, upgrade of pip and pip install (only if requirements.txt changed, or always
# with --force), migrate, collectstatic, check --deploy, restart of the service and a request
# to the login page through gunicorn.
# The application steps run as the owner of <base>/app. See common.sh for JUDGE_BASE and SERVICE.
set -euo pipefail
. "$(dirname "$0")/common.sh"

FORCE=${1:-}
require_root
require_install env

step "Descargando cambios"
OLD=$(as_owner git -C "$APP" rev-parse HEAD)
as_owner git -C "$APP" pull --ff-only
NEW=$(as_owner git -C "$APP" rev-parse HEAD)
if [ "$OLD" = "$NEW" ]; then
    echo "No hay commits nuevos."
    [ "$FORCE" = "--force" ] || { echo "Nada que hacer (usa --force para repetir los pasos)."; exit 0; }
else
    as_owner git -C "$APP" log --oneline "$OLD..$NEW"
fi

if [ "$FORCE" = "--force" ] || ! as_owner git -C "$APP" diff --quiet "$OLD" "$NEW" -- requirements.txt; then
    step "Instalando dependencias"
    as_owner "$BASE/venv/bin/pip" install --upgrade pip
    as_owner "$BASE/venv/bin/pip" install -r "$APP/requirements.txt"
fi

step "Migraciones"
manage migrate --noinput

step "Ficheros estáticos"
manage collectstatic --noinput

step "Comprobación de la configuración"
manage check --deploy

restart_and_check
