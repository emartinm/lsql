# Guía de desarrollo

## Pasos previos

* Se recomienda usar del editor de Python **PyCharm** (https://www.jetbrains.com/pycharm/) 
en su versión *Community* (gratuita).
* Es necesario disponer de un servidor de PostgreSQL 12 y otro de Oracle 11g XE, no importa si es en local o en remoto.
* Las versiones de Python consideradas para el sistema son la 3.7 y la 3.8.
* Para conectar con Oracle, además del paquete Python cx_Oracle, es necesario instalar Oracle Instant Client
  tal y como se explica en https://cx-oracle.readthedocs.io/en/latest/user_guide/installation.html#quick-start-cx-oracle-installation.
* Crear en la carpeta **venv** un *virtual environment* e instalar todas las dependencias:
    ````
    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt
    ````
* Definir las siguientes variables de entorno. Lo más cómodo es crear un script **env.sh** que exporte todo de golpe. 
  Se pueden ver valores de ejemplo de estas variables de entorno en el fichero `.travis.yml`.
  * ORACLE_MAX_GESTOR_CONNECTIONS *(conexiones simultáneas que soportará Oracle)*
  * ORACLE_GESTOR_POOL_TIMEOUT_MS *(tiempo en ms que esperará una conexión a Oracle, para cuando la cola esté llena)*
  * ORACLE_STMT_TIMEOUT_MS *(tiempo en ms que esperará un comando SQL en Oracle a su resultado)*
  * ORACLE_SERVER *(URL del servidor Oracle, usualmente `localhost`)*
  * ORACLE_PORT= *(puerto del servidor Oracle, usualmente `1521`)*
  * ORACLE_SID *(nombre de la base de datos Oracle, normalmente `xe`)*
  * ORACLE_TABLESPACE *(nombre del tablespace que has creado en Oracle, que puede ser `USERS` si no has creado ningún
  tablespace expresamente para esto)*
  * ORACLE_USER *(usuario Oracle con permisos para crear otros usuarios, puede ser `SYSTEM` si no has creado un usuario
    expresamente para esto)*
  * ORACLE_PASS *(contraseña del usuario Oracle anterior)*
  * ORACLE_MAX_COLS *(máximo número de columnas que puede tener el resultado de un ejercicio)*
  * ORACLE_MAX_ROWS *(máximo número filas que puede tener el resultado de un ejercicio)*
  * ORACLE_MAX_TABLES *(máximo número de tablas que puede tener el resultado de un ejercicio)*
  * PG_USER *(usuario PostgreSQL, usualmente `postgres`)*
  * PG_PASS *(la contraseña del usuario PostgreSQL)*
  * PG_SERVER *(URL del servidor PostgreSQL, usualmente `localhost`)*
  * PG_PORT *(puerto del servidor PostgreSQL, usualmente `5432`)*
  * PG_DB *(nombre de la base de datos PostgreSQL a usar, usualmente `postgres`)*
  
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
 