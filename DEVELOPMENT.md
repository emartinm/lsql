# Guía de desarrollo

## Pasos previos

* Se recomienda usar del editor de Python **PyCharm** (https://www.jetbrains.com/pycharm/) 
en su versión *Community* (gratuita).
* Es necesario disponer de un servidor de PostgreSQL 12 y otro de Oracle 11g XE, no importa si es en local o en remoto.
* Las versiones de Python consideradas para el sistema son la 3.7 y la 3.8, pero **mejor 3.8**.
* Para conectar con Oracle, además del paquete Python `cx_Oracle`, es necesario instalar Oracle Instant Client
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

# Incorporar cambios al proyecto
* **[LEER PRIMERO]** Hay un tutorial bastante fácil de seguir sobre como realizar *pull requests*
en proyectos GitHub en https://www.freecodecamp.org/news/how-to-make-your-first-pull-request-on-github-3/

Antes de integrar cualquier cambio en la rama principal o de hacer ningún *pull request* es necesario que:
 1. El código obtengan un 10.0 en pylint:
````
$ ./pylint.sh
------------------------------------

Your code has been rated at 10.00/10
````
 2. Los tests tengan una cobertura de código del 100%:
````
$ ./tests.sh
----------------------------------------------------------------------
(...)
Ran 26 tests in 139.763s

OK
Destroying test database for alias 'default'...
Name                     Stmts   Miss  Cover   Missing
------------------------------------------------------
judge/admin.py              45      0   100%
judge/apps.py                3      0   100%
judge/exceptions.py          9      0   100%
judge/feedback.py           78      0   100%
judge/forms.py              13      0   100%
judge/models.py            237      0   100%
judge/oracle_driver.py     385      0   100%
judge/parse.py             188      0   100%
judge/types.py              52      0   100%
judge/urls.py                6      0   100%
judge/views.py              84      0   100%
------------------------------------------------------
TOTAL                     1100      0   100%
````

# Trabajar con *forks* y ramas
Para evitar que los *pull request* acaben con muchos *commits* según avanza el tiempo
y para tener el histórico de *git* lo más limpio posible, los cambios se realizarán
en ramas que crearéis para cada una de ellos y **nunca en la rama *main***. 
La idea es que **NUNCA** hagáis cambios directamente en la rama *main* sino que esta se 
quede siempre como una copia de *upstream*. Este flujo de trabajo se conoce como *fork-and-branch* 
y podéis encontrar más información en 
https://blog.scottlowe.org/2015/01/27/using-fork-branch-git-workflow/

Primero algo de terminología:
 * *origin*: nombre del enlace a vuestro repositorio remoto *fork*
 * *upstream*: nombre del enlace al repositorio remoto principal
 * *main*: rama de vuestro *fork* en la que nunca trabajaréis y que únicamente usáis para 
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

## Paso 4: Actualizar vuestra rama *main* local
Antes de empezar, actualizar vuestra rama *main* desde *upstream* para 
tener la última versión del código

    $ git pull upstream main
    $ git push origin main

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
en *main* usando el comando: 

    $ git branch
    * <nombre_rama>
      main

Si no estáis en la rama adecuada cambiar con:

    $ git checkout <nombre_rama>

Los cambios se suben de la manera usual:

    $ git add <ficheros cambiados> 
    $ git commit
    $ git push origin <nombre_rama>  # Subir cambios al repositorio remoto del fork (origin)
    
**MUY IMPORTANTE**: en cualquier momento que haya cambios en *upstream* debéis
actualizar vuestra rama *main* desde *upstream* y luego actualizar la rama de trabajo
desde vuestra rama *main* (en ese orden):

    $ git fetch upstream                # Descarga cambios en upstream
    $ git checkout main                 # Cambia a rama main
    $ git merge upstream/main           # Fusiona lo nuevo de upstream en main
    $ git merge checkout <nombre_rama>  # Cambia a rama de trabajo
    $ git merge main                    # Fusiona la rama de trabajo con los nuevos 
                                        # cambios de "upstream" que están en "main". 

Si aparecen conflictos en algún fichero durante el último comando debéis 
editar ese fichero a mano para resolverlos **a mano** y hacer *commit*.
    
## Paso 7: Crear *pull request*
Después de haber hecho varios *commit*, haber pasado **pylint** y el 100% en los tests y haber
subido los cambios al *fork* (*origin*) dentro de una rama, hay que hacer un **PR de esa rama**. 
Para ello vais a la web de vuestro *fork* en GitHub, seleccionáis la rama concreta y pulsáis el botón 
para crear el *pull request*

## Paso 8: Corregir el *pull request*
Si se solicitan cambios (lo más usual), debéis modificar los ficheros como en el paso 6 y 
subirlos de nuevo a vuestro *fork*.

## Paso 9: Limpieza
Cuando se acepte el *pull request* tenéis que actualizar vuestra rama *main* desde *upstream*
para que reciba vuestros cambios aceptados. 

    $ git fetch upstream                      # Actualiza tu rama main local desde upstream (con el PR integrado)
    $ git checkout main
    $ git merge upstream/main                
    $ git push origin main                    # Actualiza la rama main remota del fork

También hay que borrar la rama que habéis creado para la mejora:

    $ git branch -D <nombre_rama>             # Borra la rama de desarrollo del repositorio local
    $ git push --delete origin <nombre_rama>  # Borra la rama <nombre_rama> también en el fork


