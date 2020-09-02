# Guía de desarrollo

## Pasos previos

* Se recomienda usar del editor de Python **PyCharm** (https://www.jetbrains.com/pycharm/) 
en su versión *Community* (gratuita).
* Es necesario disponer de un servidor de PostgreSQL 12 y otro de Oracle 11g XE, no importa si es en local o en remoto.
* Las versiones de Python consideradas para el sistema son la 3.7 y la 3.8.
* Crear en la carpeta **venv** un *virtual environment* e instalar todas las dependencias:
    ````
    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt
    ````
* Definir las siguientes variables de entorno. Lo más cómodo es crear un script **env.sh** que exporte todo de golpe.
  * ORACLE_MAX_GESTOR_CONNECTIONS=20
  * ORACLE_GESTOR_POOL_TIMEOUT_MS=20000
  * ORACLE_STMT_TIMEOUT_MS=1500
  * ORACLE_SERVER=**servidor Oracle, usualmente "localhost"**
  * ORACLE_PORT=**puerto de Oracle, usualmente 1521**
  * ORACLE_SID=xe
  * ORACLE_TABLESPACE=**nombre del tablespace que hayas creado en Oracle**
  * ORACLE_USER=**usuario Oracle con permisos para crear otros usuarios**
  * ORACLE_PASS=**contraseña del usuario Oracle anterior**
  * ORACLE_MAX_COLS=20
  * ORACLE_MAX_ROWS=1000
  * ORACLE_MAX_TABLES=20
  * PG_USER=**usuario PostgreSQL, usualmente "postgres"**
  * PG_PASS=**la contraseña de tu usuario PostgreSQL**
  * PG_SERVER=**servidor con PostgreSQL, usualmente "localhost"**
  * PG_PORT=**puerto de PostgreSQL, usualmente 5432**
  * PG_DB=**BD PostgreSQL a usar, usualmente "postgres"**
  
## Lanzar el servidor en local
Asegurarse de que están aplicadas todas las migraciones de la BD:
````
$ python manage.py makemigrations
$ python manage.py migrate
````
Colocar los ficheros estáticos en su lugar:
````
$ python manage.py collectstatic
````
Lanzar el servidor en local:
````
$ python manage.py runserver
````

# Pruebas a pasar
Antes de integrar cambios en la rama principal y de hacer ningún *pull request* es necesario que:
1. El código obtengan un 10.0 en pylint:
````
$ ./pylint.sh
````
1. Los tests tengan una alta cobertura de código, idealmente el 100%:
````
$ ./tests.sh
````
 