#!/bin/bash
# Backup of everything needed to rebuild the judge: the whole PostgreSQL database (problems,
# collections, users, groups, submissions, achievements...) dumped with pg_dump, the
# configuration <base>/env and the deployed commit. Run it as root (the judge keeps working):
#   sudo <base>/app/deploy/backup.sh
# It writes <base>/backups/lsql-<date>_<time>.tar (BACKUP_DIR changes the directory)
# and removes the backups older than KEEP_DAYS days (92 by default).
# The backup contains the secrets of <base>/env and personal data of the students: it is
# readable only by BACKUP_OWNER (by default, the user that runs sudo), who can copy it to
# another machine (rsync). Restore it with restore.sh. See common.sh for the other variables.
# Oracle is not included: it only holds the temporary users where submissions are executed.
set -euo pipefail
. "$(dirname "$0")/common.sh"

require_root
require_install env
BACKUP_DIR=${BACKUP_DIR:-$BASE/backups}
KEEP_DAYS=${KEEP_DAYS:-92}
BACKUP_OWNER=${BACKUP_OWNER:-${SUDO_USER:-root}}
NAME=lsql-$(date +%F_%H%M%S)

umask 077
install -d -m 700 -o "$BACKUP_OWNER" "$BACKUP_DIR"
TMP=$(mktemp -d "$BACKUP_DIR/.tmp.XXXXXX")
trap 'rm -rf "$TMP"' EXIT
mkdir "$TMP/$NAME"

step "Volcando la base de datos $(env_value PG_DB)"
pg pg_dump --format=custom >"$TMP/$NAME/db.dump"
# The dump must be readable by pg_restore
docker run --rm -i "$PG_IMAGE" pg_restore --list <"$TMP/$NAME/db.dump" >/dev/null ||
    fail "el volcado no es válido"

step "Configuración y versión"
cp "$BASE/env" "$TMP/$NAME/env"
{
    echo "date: $(date -Iseconds)"
    echo "commit: $(as_owner git -C "$APP" rev-parse HEAD)"
    echo "version: $(as_owner git -C "$APP" log -1 --format='%h %s')"
} >"$TMP/$NAME/info.txt"
cat "$TMP/$NAME/info.txt"

tar -C "$TMP" -cf "$TMP/$NAME.tar" "$NAME"
chown "$BACKUP_OWNER" "$TMP/$NAME.tar"
mv "$TMP/$NAME.tar" "$BACKUP_DIR/"

step "Borrando las copias de más de $KEEP_DAYS días"
find "$BACKUP_DIR" -maxdepth 1 -name 'lsql-*.tar' -mtime "+$KEEP_DAYS" -print -delete

echo
echo "OK: $BACKUP_DIR/$NAME.tar ($(du -h "$BACKUP_DIR/$NAME.tar" | cut -f1))"
