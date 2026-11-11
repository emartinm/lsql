# Guía de desarrollo

## Requisitos

- **Python 3.13** o posterior (es la versión de la integración continua y del despliegue).
- **Docker**, para ejecutar PostgreSQL y Oracle en contenedores desechables.
- **Oracle Instant Client** (19 o posterior): el juez usa `oracledb` en modo *thick*
  (`oracledb.init_oracle_client()`), que necesita sus bibliotecas. Descarga el paquete *Basic* de
  https://www.oracle.com/database/technologies/instant-client/linux-x86-64-downloads.html,
  descomprímelo (por ejemplo en `~/lib/instantclient_23_x`) y añade su directorio a
  `LD_LIBRARY_PATH`. `install_oracle_instant_client.sh` hace lo mismo en `/tmp` (lo usa la
  integración continua).
- **libaio**, que necesita Instant Client:
  - Ubuntu 22.04 o anterior: `sudo apt install libaio1`.
  - Ubuntu 24.04 o posterior: el paquete se llama `libaio1t64` e instala `libaio.so.1t64`, pero
    Instant Client busca `libaio.so.1`, así que hace falta un enlace en un directorio de
    `LD_LIBRARY_PATH` (o en el del sistema):
    ```sh
    sudo apt install libaio1t64
    ln -s /usr/lib/x86_64-linux-gnu/libaio.so.1t64 ~/lib/libaio.so.1
    ```
  Si falta, al conectar con Oracle aparece `DPI-1047: Cannot locate a 64-bit Oracle Client
  library: "libaio.so.1: cannot open shared object file"`.
- **DES** (Datalog Educational System), para la retroalimentación adicional de las consultas:
  descarga la versión para Linux de https://des.sourceforge.io/ (la misma que
  `install_des.sh`) y descomprímela en `des/` dentro del repositorio (está en `.gitignore`).
  `DES_BIN` debe apuntar a `des/des_start`.

## Entorno

```sh
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

Toda la configuración se lee de variables de entorno (`lsql/lsql/settings_shared.py`,
`settings_dev.py` y `settings_deploy.py`). Con `DJANGO_DEVELOPMENT` definida se usa la
configuración de desarrollo; sin ella, la de despliegue (que además exige `ALLOWED_HOSTS`).

| Variable | Significado |
|---|---|
| `SECRET_KEY` | Clave de Django (obligatoria) |
| `DJANGO_DEVELOPMENT` | Cualquier valor: configuración de desarrollo (`DEBUG`) |
| `PG_SERVER`, `PG_PORT`, `PG_DB`, `PG_USER`, `PG_PASS` | Conexión a PostgreSQL (datos del juez) |
| `ORACLE_SERVER`, `ORACLE_PORT`, `ORACLE_SERVICE_NAME` | Conexión a Oracle. El nombre de servicio es `XE` en Oracle XE y `FREEPDB1` en Oracle Free |
| `ORACLE_USER`, `ORACLE_PASS` | Usuario de Oracle que crea los usuarios temporales de cada envío (p. ej. `SYSTEM`) |
| `ORACLE_TABLESPACE` | *Tablespace* de esos usuarios (`USERS`) |
| `ORACLE_MAX_GESTOR_CONNECTIONS` | Conexiones del pool de Oracle (por proceso) |
| `ORACLE_GESTOR_POOL_TIMEOUT_MS` | Espera máxima por una conexión libre del pool |
| `ORACLE_STMT_TIMEOUT_MS` | Tiempo máximo de cada sentencia de un envío |
| `ORACLE_MAX_ROWS`, `ORACLE_MAX_COLS`, `ORACLE_MAX_TABLES` | Límites del resultado de un envío |
| `DES_BIN`, `DES_TIMEOUT` | Ejecutable de DES y su tiempo máximo en segundos |
| `LD_LIBRARY_PATH` | Debe incluir Instant Client (y el enlace a `libaio.so.1` si hace falta) |

Lo más cómodo es un script `config.sh` (no se sube al repositorio: está en `.gitignore`) que
exporte las variables, arranque las bases de datos en Docker y active el entorno virtual. Por
ejemplo:

```sh
export SECRET_KEY=clave-de-desarrollo
export DJANGO_DEVELOPMENT=true

export PG_SERVER=localhost PG_PORT=5432 PG_DB=postgres PG_USER=postgres PG_PASS=postgres
export ORACLE_SERVER=localhost ORACLE_PORT=1521 ORACLE_SERVICE_NAME=XE ORACLE_TABLESPACE=USERS
export ORACLE_USER=SYSTEM ORACLE_PASS=oracle
export ORACLE_MAX_GESTOR_CONNECTIONS=20 ORACLE_GESTOR_POOL_TIMEOUT_MS=20000 ORACLE_STMT_TIMEOUT_MS=1500
export ORACLE_MAX_COLS=30 ORACLE_MAX_ROWS=1000 ORACLE_MAX_TABLES=30
export DES_BIN=$PWD/des/des_start DES_TIMEOUT=5

docker run --rm -d --name lsql-pg -p 127.0.0.1:${PG_PORT}:5432 -e POSTGRES_PASSWORD=${PG_PASS} postgres:16
docker run --rm -d --name lsql-oracle --shm-size=2g -p 127.0.0.1:${ORACLE_PORT}:1521 \
    -e ORACLE_PASSWORD=${ORACLE_PASS} gvenzl/oracle-xe:21-slim-faststart

source venv/bin/activate
```

Oracle tarda uno o dos minutos en arrancar: espera a que `docker logs lsql-oracle` muestre
`DATABASE IS READY TO USE!`. También sirve la imagen `gvenzl/oracle-free:slim-faststart`, con
`ORACLE_SERVICE_NAME=FREEPDB1` (su base de datos *pluggable*: en la raíz de Oracle Free no se pueden
crear los usuarios de los envíos). Los contenedores no guardan datos (`--rm` sin volúmenes): para conservar la
base de datos de PostgreSQL entre sesiones, añade un volumen
(`-v $PWD/postgres:/var/lib/postgresql`; `postgres/` está en `.gitignore`).

## Lanzar el servidor en local

```sh
source config.sh
cd lsql
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver        # http://localhost:8000/sql/ (administración en /sql/admin/)
```

`launch.sh` hace lo mismo leyendo las variables de un fichero `.env` (formato `CLAVE=valor`,
también en `.gitignore`).

Otros comandos útiles (desde `lsql/`):

```sh
python manage.py makemigrations    # generar migraciones tras cambiar models.py
python manage.py dbshell           # consola SQL de PostgreSQL
python manage.py shell             # consola de Python con Django (utilidades en judge/shell.py)
python manage.py collectstatic     # copiar los estáticos a allstaticfiles/
python manage.py check --deploy    # revisar la configuración de despliegue (sin DJANGO_DEVELOPMENT)
python manage.py makemessages -l en && python manage.py compilemessages   # traducciones (locale/)
```

## Calidad

Antes de integrar cualquier cambio en la rama principal o de hacer un *pull request*:

1. Las pruebas pasan con un **100 % de cobertura**. Se ejecutan contra PostgreSQL, Oracle y DES
   reales (no hay simulaciones), así que necesitan el entorno anterior:
   ```sh
   ./tests.sh          # coverage run manage.py test + informe con las líneas sin cubrir
   ```
   Para una parte: `cd lsql && python manage.py test judge.tests.test_models` (o
   `judge.tests.test_models.SelectProblemTestCase.test_judge_ac`).
2. `./ruff.sh` sin avisos (configuración en `ruff.toml`).
3. `./bandit.sh` sin avisos.

La integración continua (`.github/workflows/`) ejecuta lo mismo en cada *push* y *pull request* a
`master`: ruff, las pruebas con PostgreSQL y Oracle XE 21 como servicios (con subida de la
cobertura a Codecov, `tests_ci.sh`), bandit y CodeQL. Dependabot propone cada semana las
actualizaciones de `requirements.txt` y de las acciones.

# Trabajar con *forks* y ramas
Para evitar que los *pull request* acaben con muchos *commits* según avanza el tiempo
y para tener el histórico de *git* lo más limpio posible, los cambios se realizarán
en ramas que crearéis para cada una de ellos y **nunca en la rama *master***. 
La idea es que **NUNCA** hagáis cambios directamente en la rama *master* sino que esta se 
quede siempre como una copia de *upstream*. Este flujo de trabajo se conoce como *fork-and-branch* 
y podéis encontrar más información en 
https://blog.scottlowe.org/2015/01/27/using-fork-branch-git-workflow/

Primero algo de terminología:
 * *origin*: nombre del enlace a vuestro repositorio remoto *fork*
 * *upstream*: nombre del enlace al repositorio remoto principal
 * *master*: rama de vuestro *fork* en la que nunca trabajaréis y que únicamente usáis para 
  sincronizar vuestra copia local con *upstream*

Para ello hay que seguir estos pasos (desde el terminal):

## Paso 1: Crear un fork en GitHub

## Paso 2: Clonar una copia local del fork
    
    $ git clone <repositorio_fork>

## Paso 3: Añadir un remoto *upstream*
El remoto *upstream* apunta al repositorio principal (no a tu *fork*). 
El otro remoto que tendréis se llama *origin* y apunta al repositorio fork 
(el que es completamente vuestro)
    
    $ git remote add upstream <repositorio_principal>

## Paso 4: Actualizar vuestra rama *master* local
Antes de empezar, actualizar vuestra rama *master* desde *upstream* para 
tener la última versión del código

    $ git pull upstream master
    $ git push origin master

## Paso 5: Crear una rama para trabajar
Cada mejora se realizará en una rama concreta. La rama se crea antes de
empezar a trabajar en la mejora y se elimina una vez los cambios se han
integrado en el repositorio principal (el *pull request* ha sido aceptado).
El nombre de la rama deberia ser algo informativo de lo que hace: "descarga_envio", 
"feedback_esquema", etc.

    $ git checkout -b <nombre_rama>
    
## Paso 6: Realizar cambios en los ficheros
Hacer cambios en los ficheros y subirlos al fork, podéis hacer varios *commit*
en la mejora sin ningún problema. Revisad que estáis trabajando en vuestra rama y no
en *master* usando el comando: 

    $ git branch
    * <nombre_rama>
      master

Si no estáis en la rama adecuada cambiar con:

    $ git checkout <nombre_rama>

Los cambios se suben de la manera usual:

    $ git add <ficheros cambiados> 
    $ git commit
    $ git push origin <nombre_rama>  # Subir cambios al repositorio remoto del fork (origin)
    
**MUY IMPORTANTE**: en cualquier momento que haya cambios en *upstream* debéis
actualizar vuestra rama *master* desde *upstream* y luego actualizar la rama de trabajo
desde vuestra rama *master* (en ese orden):

    $ git fetch upstream                # Descarga cambios en upstream
    $ git checkout master               # Cambia a rama master
    $ git merge upstream/master         # Fusiona lo nuevo de upstream en master
    $ git merge checkout <nombre_rama>  # Cambia a rama de trabajo
    $ git merge master                  # Fusiona la rama de trabajo con los nuevos 
                                        # cambios de "upstream" que están en "master". 

Si aparecen conflictos en algún fichero durante el último comando debéis 
editar ese fichero a mano para resolverlos **a mano** y hacer *commit*.
    
## Paso 7: Crear *pull request*
Después de haber hecho varios *commit*, haber pasado **ruff** y **bandit** sin avisos y el 100 % de cobertura en los tests y haber
subido los cambios al *fork* (*origin*) dentro de una rama, hay que hacer un **PR de esa rama**. 
Para ello vais a la web de vuestro *fork* en GitHub, seleccionáis la rama concreta y pulsáis el botón 
para crear el *pull request*

## Paso 8: Corregir el *pull request*
Si se solicitan cambios (lo más usual), debéis modificar los ficheros como en el paso 6 y 
subirlos de nuevo a vuestro *fork*.

## Paso 9: Limpieza
Cuando se acepte el *pull request* tenéis que actualizar vuestra rama *master* desde *upstream*
para que reciba vuestros cambios aceptados. 

    $ git fetch upstream                      # Actualiza tu rama master local desde upstream (con el PR integrado)
    $ git checkout master
    $ git merge upstream/master                
    $ git push origin master                  # Actualiza la rama master remota del fork

También hay que borrar la rama que habéis creado para la mejora:

    $ git branch -D <nombre_rama>             # Borra la rama de desarrollo del repositorio local
    $ git push --delete origin <nombre_rama>  # Borra la rama <nombre_rama> también en el fork


