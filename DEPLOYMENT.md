# Despliegue

LearnSQL se sirve bajo la ruta `/sql/` de su dominio, detrás de un proxy inverso con TLS
(nginx) y con gunicorn gestionado por systemd. Puede compartir dominio y servidor con otras
aplicaciones Django (por ejemplo, [haskell-judge](https://github.com/emartinm/haskell-judge)
bajo `/haskell/`): cada una tiene su usuario del sistema, su directorio, su entorno virtual, su
servicio, su puerto local de gunicorn y su base de datos.

Requisitos: Python 3.13 o posterior, PostgreSQL, Oracle (con
[Oracle Instant Client](https://www.oracle.com/database/technologies/instant-client.html)
instalado, porque `oracledb` se usa en modo *thick*; necesita también `libaio`: paquete `libaio1`, o
`libaio1t64` en Ubuntu 24.04 o posterior con un enlace `libaio.so.1`), el ejecutable de
[DES](https://des.sourceforge.io/), Docker (solo para las copias de seguridad) y nginx.

Las plantillas están en `deploy/`; en los ejemplos, `<usuario>` es el usuario del sistema que
ejecuta el juez y `<base>` su directorio, con esta estructura:

```
<base>/app      este repositorio
<base>/venv     entorno virtual
<base>/env      configuración (deploy/env.example), legible solo por <usuario>
<base>/des      DES (DES_BIN)
<base>/backups  copias de seguridad (deploy/backup.sh)
```

## Instalación

1. **Usuario** del sistema, sin sesión ni contraseña:
   ```sh
   sudo adduser --system --group --home <base> --shell /usr/sbin/nologin <usuario>
   ```
2. **Configuración** con claves aleatorias (completa los valores de `deploy/env.example`:
   nombre del servidor, puerto local de gunicorn —distinto del de las otras aplicaciones del
   servidor—, conexión a PostgreSQL y a Oracle, y ruta de DES):
   ```sh
   sudo -u <usuario> sh -c 'umask 077; cat > <base>/env' <<EOF
   ALLOWED_HOSTS=...
   GUNICORN_BIND=127.0.0.1:...
   SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
   PG_DB=lsql
   PG_USER=lsql
   PG_PASS=$(openssl rand -hex 24)
   PG_SERVER=...
   PG_PORT=...
   ORACLE_SERVER=...
   ...
   DES_BIN=<base>/des/des_start
   DES_TIMEOUT=5
   SENTRY_DSN=
   EOF
   ```
3. **Base de datos**: crea en PostgreSQL el usuario `lsql`, con la contraseña `PG_PASS` del
   fichero anterior, y la base de datos `lsql` cuyo propietario sea ese usuario. Puede ser el
   mismo servidor de PostgreSQL que usen otras aplicaciones (con otra base de datos).
4. **Código, entorno virtual y DES**:
   ```sh
   sudo -u <usuario> git clone https://github.com/emartinm/lsql.git <base>/app
   sudo -u <usuario> python3 -m venv <base>/venv
   sudo -u <usuario> <base>/venv/bin/pip install -r <base>/app/requirements.txt
   ```
   Descomprime DES en `<base>/des` (debe poder ejecutarlo `<usuario>`).
5. **Base de datos, estáticos y comprobaciones** (`deploy/manage.sh` ejecuta `manage.py` con la
   configuración de `<base>/env`):
   ```sh
   sudo -u <usuario> <base>/app/deploy/manage.sh migrate
   sudo -u <usuario> <base>/app/deploy/manage.sh collectstatic --noinput
   sudo -u <usuario> <base>/app/deploy/manage.sh check --deploy
   sudo -u <usuario> <base>/app/deploy/manage.sh createsuperuser
   ```
6. **Servicio**: adapta `deploy/lsql.service.example` (usa `deploy/gunicorn.conf.py`), cópialo
   a `/etc/systemd/system/lsql.service` y
   `sudo systemctl daemon-reload && sudo systemctl enable --now lsql`.
7. **nginx**: añade `deploy/nginx.conf.example`, adaptado, al bloque `server` de HTTPS del
   dominio y después `sudo nginx -t && sudo systemctl reload nginx`.

## Actualizar

```sh
sudo <base>/app/deploy/update.sh            # solo si hay commits nuevos
sudo <base>/app/deploy/update.sh --force    # repite todos los pasos aunque no los haya
```

Descarga los cambios (`git pull --ff-only`), actualiza pip y las dependencias si ha cambiado
`requirements.txt` (siempre con `--force`), aplica las migraciones, recoge los estáticos, ejecuta
`check --deploy`, reinicia el servicio y comprueba que la página de entrada responde a través de
gunicorn. Si el servicio no se llama `lsql`: `sudo SERVICE=<nombre> <base>/app/deploy/update.sh`.

A mano:
```sh
sudo -u <usuario> git -C <base>/app pull
sudo -u <usuario> <base>/venv/bin/pip install --upgrade pip
sudo -u <usuario> <base>/venv/bin/pip install -r <base>/app/requirements.txt
sudo -u <usuario> <base>/app/deploy/manage.sh migrate
sudo -u <usuario> <base>/app/deploy/manage.sh collectstatic --noinput
sudo systemctl restart lsql
```

## Copias de seguridad

`deploy/backup.sh` guarda la base de datos de PostgreSQL completa (problemas, colecciones,
usuarios, grupos, envíos, logros…) volcada con `pg_dump`, la configuración `<base>/env` y el
commit desplegado. Oracle no se copia: solo contiene los usuarios temporales donde se ejecutan
los envíos. El juez sigue funcionando mientras tanto.

```sh
sudo <base>/app/deploy/backup.sh      # → <base>/backups/lsql-<fecha>_<hora>.tar
```

- `pg_dump` y `pg_restore` se ejecutan en un contenedor temporal de la imagen `postgres:16`
  (variable `PG_IMAGE`: debe ser de la misma versión principal que el servidor de PostgreSQL).
- Borra las copias de más de 92 días (`KEEP_DAYS`). El directorio se cambia con `BACKUP_DIR`.
- La copia contiene los secretos de `<base>/env` y datos personales de los estudiantes: solo la
  puede leer `BACKUP_OWNER` (por defecto, el usuario que ejecuta `sudo`).

`deploy/restore.sh` **sustituye** la base de datos del juez por la de una copia (antes guarda una
copia del estado actual, pide confirmación salvo con `--yes`, para el servicio, carga el
volcado, aplica las migraciones y vuelve a arrancar y comprobar el juez):

```sh
sudo <base>/app/deploy/restore.sh <base>/backups/lsql-<fecha>_<hora>.tar
```

## Convivencia con otras aplicaciones en el mismo dominio

- Rutas: LearnSQL atiende `/sql/` y sus estáticos están en `/static/` (`STATIC_URL`); haskell-judge
  usa `/haskell/` y `/haskell/static/`.
- Cookies: LearnSQL usa los nombres por defecto de Django (`sessionid`, `csrftoken`);
  haskell-judge usa nombres propios (`haskell_sessionid`, `haskell_csrftoken`) con ruta
  `/haskell/`, así que no se pisan.
- Cada aplicación tiene su propio servicio systemd, puerto de gunicorn (`GUNICORN_BIND`),
  usuario, entorno virtual y base de datos, de modo que se actualizan por separado con su
  propio `deploy/update.sh`.
