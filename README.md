
# Learn SQL
![build status](https://github.com/emartinm/lsql/actions/workflows/django_tests.yml/badge.svg)
![Ruff status](https://github.com/emartinm/lsql/actions/workflows/ruff.yml/badge.svg)
[![codecov](https://codecov.io/gh/emartinm/lsql/branch/master/graph/badge.svg)](https://codecov.io/gh/emartinm/lsql)

Juez automático en Django para aprender bases de datos con SQL y PL/SQL: colecciones de
problemas, envíos con veredicto, pistas, logros, clasificaciones y estadísticas. Los envíos se
ejecutan en Oracle, cada uno en un usuario temporal propio, y opcionalmente se analizan con
[DES](https://des.sourceforge.io/) (Datalog Educational System) para dar más retroalimentación.
Se sirve bajo la ruta `/sql/` de su dominio, de modo que puede compartirlo con otras aplicaciones
(por ejemplo, [haskell-judge](https://github.com/emartinm/haskell-judge) bajo `/haskell/`).

Documentación relacionada:
- [DEVELOPMENT.md](DEVELOPMENT.md): entorno de desarrollo, pruebas y flujo de trabajo con Git.
- [DEPLOYMENT.md](DEPLOYMENT.md): despliegue, actualización y copias de seguridad en producción.

## Funcionalidad

- **Estudiantes**: colecciones de problemas con su progreso, página de problema con el enunciado,
  las tablas de la base de datos inicial y el resultado esperado, envíos con veredicto y
  retroalimentación (diferencias con el resultado esperado, errores de Oracle con su posición y
  avisos de DES), historial de envíos, pistas que se desbloquean tras varios envíos, logros y
  clasificación por grupo. Interfaz en español e inglés.
- **Profesores** (usuarios *staff*): administración de Django (`/sql/admin/`) para colecciones,
  problemas, pistas y logros; importación de problemas desde ZIP; clasificación de cualquier
  grupo con descarga en ODS; estadísticas de envíos y de participación; filtro de colecciones por
  profesor.
- **Validación al guardar**: al guardar un problema se ejecuta su solución de referencia en Oracle
  y se guarda el resultado esperado. Si la solución falla, el problema no se guarda.
- **Límites**: tiempo por sentencia (`ORACLE_STMT_TIMEOUT_MS`), número máximo de filas, columnas y
  tablas del resultado, un solo envío simultáneo por usuario y bloqueo temporal tras varios
  intentos de acceso fallidos (django-axes).

### Tipos de problema y veredictos

| Tipo | El estudiante envía | Se compara |
|---|---|---|
| SELECT | Una consulta | Su resultado con el de la solución, en una o varias bases de datos |
| DML | Sentencias `INSERT`/`UPDATE`/`DELETE`/`CREATE`… | El estado de la base de datos tras ejecutarlas |
| Función | Una función PL/SQL | El valor devuelto en cada llamada de `tests.sql` |
| Procedimiento | Un procedimiento PL/SQL | El estado de la base de datos tras la llamada de `tests.sql` |
| Disparador | Un disparador PL/SQL | El estado de la base de datos tras las sentencias de `tests.sql` |
| Discriminante | Sentencias `INSERT` | Que la consulta incorrecta y la correcta del problema den resultados distintos |

Veredictos: `AC` (aceptado), `WA` (resultados incorrectos), `RE` (error en ejecución),
`TLE` (tiempo límite excedido), `VE` (error de validación, p. ej. número de sentencias fuera del
rango del problema) e `IE` (error interno).

## Estructura

```
lsql/lsql/              configuración de Django (settings_shared/dev/deploy, urls)
lsql/judge/             la aplicación
  models.py             Collection, Problem y sus subclases, Submission, Hint, logros
  oracle_driver.py      ejecución en Oracle (usuarios temporales, límites, resultados)
  des_driver.py         análisis de consultas con DES
  feedback.py           comparación de resultados y retroalimentación en HTML
  parse.py              importación de problemas desde ZIP
  statistics.py         consultas agregadas para las estadísticas
  shell.py              utilidades para "manage.py shell" (rejuzgar, informes, análisis SQL)
  management/commands/create_users.py   alta de estudiantes desde el CSV de la UCM
  views.py, admin.py    vistas y administración
  tests/                pruebas (con PostgreSQL, Oracle y DES reales)
deploy/                 scripts y plantillas de despliegue (ver DEPLOYMENT.md)
```

## Desarrollo

Requisitos: Python 3.13 o posterior, Docker (PostgreSQL y Oracle en contenedores),
[Oracle Instant Client](https://www.oracle.com/database/technologies/instant-client.html) con
`libaio` y DES. Los pasos detallados están en [DEVELOPMENT.md](DEVELOPMENT.md).

```sh
python3 -m venv venv && venv/bin/pip install -r requirements.txt
source config.sh                 # entorno, PostgreSQL y Oracle en Docker (ver DEVELOPMENT.md)
cd lsql
python manage.py migrate
python manage.py createsuperuser
cd .. && ./launch.sh             # http://localhost:8000/sql/
```

Calidad (lo mismo que comprueba la integración continua):

```sh
./tests.sh       # pruebas con cobertura (debe ser 100 %); necesita PostgreSQL, Oracle y DES
./ruff.sh        # estilo
./bandit.sh      # análisis de seguridad
```

## Problemas

Se crean desde la administración (`/sql/admin/`): cada tipo de problema tiene su formulario, donde
se pueden rellenar los campos a mano o subir un ZIP (que sobrescribe los campos). Para importar
varios problemas a la vez, edita una colección y sube en su campo ZIP un fichero que contenga un
ZIP por problema: se añaden todos a esa colección, y si alguno falla no se guarda ninguno.

Formato del ZIP de un problema (todo en UTF-8; se admite BOM):

| Fichero | Contenido |
|---|---|
| `problem.json` | `{"type": 0, "title": "Filtrar columnas", "position": 2, "min_stmt": 1, "max_stmt": 1, "check_order": false, "language": "es"}` |
| `text.md` | Enunciado (Markdown) |
| `create.sql` | Creación de las tablas |
| `insert.sql` | Datos iniciales |
| `solution.sql` | Solución de referencia (todos los tipos salvo discriminante) |
| `tests.sql` | Función, procedimiento y disparador: las pruebas (ver abajo) |
| `correct_query.sql`, `incorrect_query.sql` | Discriminante: consulta correcta y consulta incorrecta |
| `hints.md` | Pistas (opcional) |

- `type`: 0 SELECT, 1 DML, 2 función, 3 procedimiento, 4 disparador, 5 discriminante.
- `title` y `position` son obligatorios. `min_stmt`/`max_stmt` (1 por defecto) es el rango de
  sentencias que puede tener un envío. `check_order` (SELECT y discriminante, `false` por defecto)
  exige que las filas salgan en el mismo orden. `language` es `es` (por defecto) o `en`.
- **SELECT con varias bases de datos**: `insert.sql` puede contener varios conjuntos de datos
  separados por una línea `-- @new data base@`. El envío debe dar el resultado correcto con todos;
  el estudiante ve el primero.
- **Función**: `tests.sql` tiene una llamada por línea (`golesLocal('2-1')`); se compara el valor
  devuelto en cada una.
- **Procedimiento**: `tests.sql` es un bloque PL/SQL que llama al procedimiento
  (`BEGIN actualiza_socios('11111111X'); END;`).
- **Disparador**: `tests.sql` son las sentencias que lo disparan.
- **Discriminante**: el estudiante envía `INSERT`s que, añadidos a los datos iniciales, hacen que
  `incorrect_query.sql` dé un resultado distinto del de `correct_query.sql`.
- **Pistas** (`hints.md`): bloques separados por `@@@new hint@@@`; cada uno empieza con el número
  de envíos necesario para desbloquearla y sigue con el texto en Markdown:
  ```
  3
  Revisa la condición del **WHERE**.
  @@@new hint@@@
  5
  Necesitas una reunión con la tabla `Club`.
  ```

En `lsql/judge/tests/zip_files/` hay ejemplos de cada tipo (`select_ok.zip`, `dml_ok.zip`,
`function_ok.zip`, `proc_ok.zip`, `trigger_ok.zip`, `discriminant_ok.zip`,
`select_with_hints.zip`, `select_multiple_db_ok.zip`, `problems.zip`…).

Las colecciones tienen nombre y descripción en Markdown, posición y visibilidad: las ocultas solo
las ven los profesores. Los logros (problemas resueltos en total, por colección o por tipo,
puestos en el podio, problemas resueltos en pocos envíos) se definen en la administración.

## Estudiantes

```sh
cd lsql
python manage.py create_users estudiantes.csv "Grupo A"          # simulación
python manage.py create_users estudiantes.csv "Grupo A" --save   # crea los usuarios
```

El CSV de la UCM debe tener las columnas `NOMBRE COMPLETO` («Apellidos, Nombre»),
`DOCUMENTO` y `CORREO`, separadas por comas (las demás columnas se ignoran). El usuario es la
parte del correo anterior a `@ucm.es` y la contraseña inicial, el documento. Los usuarios
existentes solo se añaden al grupo (no cambia su contraseña), así que se puede repetir la
importación o importar a un estudiante en varios grupos. Si alguna fila es incorrecta (por
ejemplo, un correo que no es de la UCM), no se guarda nada. Los grupos son las «clases» de la
clasificación: los profesores también deben pertenecer a sus grupos.

En producción, con el usuario del juez. El CSV contiene los documentos de identidad: déjalo
legible solo por ese usuario y bórralo al terminar.

```sh
sudo install -o <usuario> -m 600 estudiantes.csv <base>/estudiantes.csv
sudo -u <usuario> <base>/app/deploy/manage.sh create_users <base>/estudiantes.csv "Grupo A"          # simulación
sudo -u <usuario> <base>/app/deploy/manage.sh create_users <base>/estudiantes.csv "Grupo A" --save   # crea los usuarios
sudo rm <base>/estudiantes.csv
```

Para cambiar la contraseña de un estudiante: administración → Usuarios → el estudiante → «Cambiar
contraseña». Los estudiantes pueden cambiarla ellos mismos desde su menú.

## Otras utilidades (`judge/shell.py`)

Se ejecutan con `manage.py shell` (en producción, `<base>/app/deploy/manage.sh shell`):

- `rejudge(VerdictCode.IE, "rejudge.txt", start=..., end=...)`: vuelve a juzgar los envíos con ese
  veredicto en el periodo indicado y escribe en el fichero los cambios de veredicto (no modifica
  los envíos guardados).
- `extended_submissions("envios.csv")`: CSV con todos los envíos de los estudiantes, con datos del
  usuario, el problema y la colección.
- `submissions_per_user("resumen.csv")`: CSV con el resumen de envíos de cada estudiante.
- `keywords(sql)`, `is_where(...)`, `is_group_by(...)`, `is_nested(...)`…: detección con
  [sqlglot](https://github.com/tobymao/sqlglot) de las construcciones SQL de un envío, para
  estudiar qué usan los estudiantes.

## Despliegue

En producción se ejecuta con gunicorn y systemd detrás de nginx, con su propio usuario, entorno
virtual y base de datos. `deploy/update.sh` actualiza a la última versión (git pull, dependencias,
migraciones, estáticos y reinicio) y `deploy/backup.sh` / `deploy/restore.sh` hacen y restauran
copias de seguridad. Todos los pasos están en [DEPLOYMENT.md](DEPLOYMENT.md).

## Equipo

LearnSQL se ha desarrollado como proyecto de código abierto con licencia MIT. Su desarrollo y
evaluación han contado con el apoyo de los proyectos de innovación docente de la Universidad
Complutense de Madrid INNOVA-Docencia 2020-21/18 (*«Juez automático para el aprendizaje de bases
de datos»*) y 2021-22/387 (*«Evaluación del impacto sobre el aprendizaje de bases de datos del
juez automático LearnSQL»*).

También han participado estudiantes de la Facultad de Informática de la Universidad Complutense
de Madrid, que han realizado mejoras en sus Trabajos de Fin de Grado.

El equipo completo que ha participado en su diseño, desarrollo y evaluación es:
- IKER BURGOA
- PABLO CERRO
- JESÚS CORREAS
- LUIS GARMENDIA
- TAMARA HUERTAS
- DANIEL IBÁÑEZ
- ENRIQUE MARTÍN
- MANUEL MONTENEGRO
- ADRIÁN RIESCO
- RUBÉN RUBIO
- IVÁN RUIZ
- FERNANDO SÁENZ

## Licencia

[MIT](LICENSE)
