# Despliegue

LearnSQL se sirve bajo la ruta `/sql/` de su dominio, detrás de un proxy inverso con TLS
(nginx) y con gunicorn gestionado por systemd. Puede compartir dominio y servidor con otras
aplicaciones Django (por ejemplo, [haskell-judge](https://github.com/emartinm/haskell-judge)
bajo `/haskell/`): cada una tiene su usuario del sistema, su directorio, su entorno virtual, su
servicio, su puerto local de gunicorn y su base de datos.

Requisitos:
- Python 3.13 o posterior.
- PostgreSQL (datos del juez: problemas, usuarios, envíos…).
- Oracle, donde se ejecutan los envíos. Lo más sencillo es Oracle XE en Docker con
  `deploy/oracle-xe.sh` (ver abajo).
- [Oracle Instant Client](https://www.oracle.com/database/technologies/instant-client.html) y
  `libaio`, porque `oracledb` se usa en modo *thick*.
- El ejecutable de [DES](https://des.sourceforge.io/).
- Docker (para Oracle y para las copias de seguridad) y nginx.

Las plantillas están en `deploy/`. En los ejemplos, `<usuario>` es el usuario del sistema que
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
2. **Configuración**: crea `<base>/env` vacío, con permisos solo para `<usuario>`, y rellénalo
   con los valores de `deploy/env.example` (nombre del servidor, puerto local de gunicorn
   —distinto del de las otras aplicaciones del servidor—, PostgreSQL, Oracle y DES):
   ```sh
   sudo install -o <usuario> -g <usuario> -m 600 /dev/null <base>/env
   sudoedit <base>/env
   ```
   Para generar claves nuevas:
   `python3 -c "import secrets; print(secrets.token_urlsafe(50))"` (`SECRET_KEY`) y
   `openssl rand -hex 24` (contraseñas).
   - El formato es el de `EnvironmentFile` de systemd: `CLAVE=valor`, sin `export` ni comillas.
     Los valores se leen literalmente (también en `deploy/manage.sh`): no se expanden `$VAR` ni
     `~`, así que `LD_LIBRARY_PATH` debe tener la lista completa de rutas.
   - Si copias claves existentes, no uses un `cat <<EOF` en la terminal: la shell expandiría los
     `$` que contengan.
3. **Base de datos**: crea en PostgreSQL el usuario `lsql`, con la contraseña `PG_PASS` del
   fichero anterior, y la base de datos `lsql` cuyo propietario sea ese usuario. Puede ser el
   mismo servidor de PostgreSQL que usen otras aplicaciones (con otra base de datos).
4. **Código y entorno virtual**:
   ```sh
   sudo -u <usuario> git clone https://github.com/emartinm/lsql.git <base>/app
   sudo -u <usuario> python3.13 -m venv <base>/venv
   sudo -u <usuario> <base>/venv/bin/pip install --upgrade pip
   sudo -u <usuario> <base>/venv/bin/pip install -r <base>/app/requirements.txt
   ```
   Si el Python del sistema es más antiguo, instala 3.13 aparte (por ejemplo, del PPA *deadsnakes*
   con `python3.13-venv`) y crea el entorno virtual con él.
5. **Oracle Instant Client y DES**, fuera de los directorios personales (los debe poder leer
   `<usuario>`):
   ```sh
   sudo mkdir -p /opt/oracle
   sudo unzip instantclient-basic-linux.x64-<versión>.zip -d /opt/oracle
   sudo ln -sfn /opt/oracle/instantclient_<versión> /opt/oracle/instantclient
   sudo apt install libaio1        # libaio1t64 en Ubuntu 24.04+, con un enlace libaio.so.1 (DEVELOPMENT.md)

   sudo unzip DESLinux64SICStus.zip -d <base>      # crea <base>/des
   sudo chown -R <usuario>:<usuario> <base>/des && sudo chmod -R go-w <base>/des
   ```
   En `<base>/env`: `LD_LIBRARY_PATH=/opt/oracle/instantclient:<base>/des/lib` y
   `DES_BIN=<base>/des/des_start`.
6. **Oracle** (si no tienes ya un servidor de Oracle): adapta `deploy/oracle-xe.service.example`,
   cópialo a `/etc/systemd/system/lsql-oracle.service` y arráncalo. Usa `ORACLE_PASS` y
   `ORACLE_PORT` de `<base>/env` (con `ORACLE_SERVER=localhost`, `ORACLE_SID=xe` y
   `ORACLE_USER=SYSTEM`). La imagen solo admite en `ORACLE_PASS` letras, números, `_` y `-`
   (con `&`, por ejemplo, falla al arrancar con `ORA-00922`); `openssl rand -hex 24` sirve:
   ```sh
   sudo systemctl daemon-reload && sudo systemctl enable --now lsql-oracle
   journalctl -u lsql-oracle -f       # espera a "DATABASE IS READY TO USE!" (1-2 minutos)
   ```
   El contenedor no guarda datos: Oracle solo contiene los usuarios temporales de los envíos.
7. **Base de datos, estáticos y comprobaciones** (`deploy/manage.sh` ejecuta `manage.py` con la
   configuración de `<base>/env`):
   ```sh
   sudo -u <usuario> <base>/app/deploy/manage.sh migrate
   sudo -u <usuario> <base>/app/deploy/manage.sh collectstatic --noinput
   sudo -u <usuario> <base>/app/deploy/manage.sh check --deploy
   sudo -u <usuario> <base>/app/deploy/manage.sh createsuperuser
   ```
   Para comprobar la conexión con Oracle (Instant Client, `LD_LIBRARY_PATH` y credenciales) y DES:
   ```sh
   sudo -u <usuario> <base>/app/deploy/manage.sh shell -c "from judge.oracle_driver import OracleExecutor; OracleExecutor.get(); print('Oracle ok')"
   sudo -u <usuario> test -x <base>/des/des_start && echo "DES ok"
   ```
8. **Servicio**: adapta `deploy/lsql.service.example` (usa `deploy/gunicorn.conf.py`), cópialo
   a `/etc/systemd/system/lsql.service` y arráncalo. Antes de configurar nginx, comprueba que
   responde directamente:
   ```sh
   sudo systemctl daemon-reload && sudo systemctl enable --now lsql
   curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: <ALLOWED_HOSTS>' -H 'X-Forwarded-Proto: https' http://<GUNICORN_BIND>/sql/login/    # 200
   ```
9. **nginx**: añade `deploy/nginx.conf.example`, adaptado, al bloque `server` de HTTPS del
   dominio y después `sudo nginx -t && sudo systemctl reload nginx`.

gunicorn (`deploy/gunicorn.conf.py`) usa 2 procesos con 8 hilos cada uno: cada envío ocupa un
hilo mientras espera a Oracle y DES. Cada proceso tiene su propio pool de
`ORACLE_MAX_GESTOR_CONNECTIONS` conexiones, así que Oracle recibe el doble.

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

**Programadas** en el crontab de root (`sudo crontab -e`). Sin `sudo` no hay `SUDO_USER`, así que
hay que indicar el propietario. Si hay otras aplicaciones con copias, ponlas a horas distintas:

```
0 3 * * 2,5  BACKUP_OWNER=<propietario> <base>/app/deploy/backup.sh >> /var/log/lsql-backup.log 2>&1
```

Para probarlo con el entorno de cron:
`sudo env -i HOME=/root PATH=/usr/bin:/bin BACKUP_OWNER=<propietario> <base>/app/deploy/backup.sh`.

**Restaurar**: `deploy/restore.sh` **sustituye** la base de datos del juez por la de una copia.
Antes guarda una copia del estado actual, pide confirmación salvo con `--yes`, para el servicio,
carga el volcado, aplica las migraciones y vuelve a arrancar y comprobar el juez:

```sh
sudo <base>/app/deploy/restore.sh <base>/backups/lsql-<fecha>_<hora>.tar
```

En un servidor nuevo: pasos 1, 4 y 5 de la instalación; después `restore.sh`, que restaura
`<base>/env` desde la copia y se detiene si no puede conectar con la base de datos; paso 3 con la
contraseña `PG_PASS` de ese `<base>/env`; `restore.sh` de nuevo y, por último, el paso 6
(Oracle), `collectstatic` y los pasos 8 y 9 (servicio y nginx).

## Problemas frecuentes

- **`DPI-1047: Cannot locate a 64-bit Oracle Client library`**: Instant Client no está en
  `LD_LIBRARY_PATH` de `<base>/env`, `<usuario>` no puede leerlo, o falta `libaio`
  (el mensaje lo nombra).
- **`ORA-12541: Cannot connect. No listener`**: Oracle está parado o aún arrancando
  (`systemctl status lsql-oracle`, `journalctl -u lsql-oracle`).
- **nginx devuelve 502**: el servicio está parado o escucha en otro puerto
  (`systemctl status lsql`, `journalctl -u lsql -n 50`, `ss -ltnp`).
- **Página sin estilos (403/404 en `/sql/static/…`)**: falta `collectstatic`, el `alias` de nginx
  apunta a otro sitio, o nginx (`www-data`) no puede atravesar `<base>` (`ls -ld <base>` debe
  dar `drwxr-xr-x`).
- **Los registros** del juez (gunicorn y Django) están en el journal: `journalctl -u lsql`. DES
  escribe además en `<base>/app/log/`.

## Convivencia con otras aplicaciones en el mismo dominio

- Rutas: LearnSQL atiende `/sql/` y sus estáticos están en `/sql/static/` (`STATIC_URL`);
  haskell-judge usa `/haskell/` y `/haskell/static/`.
- Cookies: LearnSQL usa los nombres por defecto de Django (`sessionid`, `csrftoken`);
  haskell-judge usa nombres propios (`haskell_sessionid`, `haskell_csrftoken`) con ruta
  `/haskell/`, así que no se pisan.
- Cada aplicación tiene su propio servicio systemd, puerto de gunicorn (`GUNICORN_BIND`),
  usuario, entorno virtual y base de datos, de modo que se actualizan por separado con su
  propio `deploy/update.sh`.
