# Tareas completadas:

## Iker

* (Jesús) [**Dificultad baja**] [IMPRESCINDIBLE] [**Tarea para Iker 28/10-15/11 PR #15**]
 Botón para descargarse el *script* de creación de las tablas y carga de datos en cada problema.
 
 * (Enrique) [**Dificultad baja**] [**IMPRESCINDIBLE**] [**Tarea para Iker 17/11-14/12 PR#19**]
Mejorar el mensaje de error cuando la consulta enviada no respeta el 
esquema esperado, para especificar cuál es el primer atributo que es
diferente. Realizar la comparación de nombres de columna sin tener 
en cuenta mayúsculas-minúsculas.

* [**Dificultad baja**] [**INTERESANTE**]  [**Tarea para Iker 21/12-25/02 PR#26**]
Al hacer clic en la celda de la tabla de clasificación llevará al listado de todos los envíos de ese usuario para ese problema.

* [**Dificultad media**] [**IMPRESCINDIBLE**]  [**Tarea para Iker 21/12-08/02**] [**No hay PR, se usa Django, comentar memoria**]
Agrupar usuarios en clases. Se podría utilizar los grupos de Django, lo que facilita bastante la cosa.

* [**Dificultad media**] [**INTERESANTE**]  [**Tarea para Iker 21/12-25/02 PR#26**]
Mostrar la clasificación de los usuarios de una clase por cada colección. Los usuarios no se mostrarán en orden,
únicamente se indicará el número de envíos y los problemas resueltos, además de información detallada de cada problema.
Permitir que los administradores vean las clasificaciones todas las clases y todos los usuarios. 
Incorporar orden al mostrar los resultados: número de problemas resueltos, número de envíos.
Un usuario puede estar en varios cursos. Staff lo ve todo.

* (Enrique y Jesús) [**Dificultad media**] [INTERESANTE] [**Tarea para Iker 26/02-09/03 PR #42**]
  En la pestaña 'Resultados' añadir un selector de fechas inicio(inicio curso) y fin (tope día de hoy) que ajuste los resultados a las fechas restringidas


## Iván

* (Enrique) [**Dificultad baja**] [**INTERESANTE**] [**Tarea para Iván 11/11-26/02/2021 PR #27**]
 Mostrar al menos las tablas de manera más compacta, p.ej. mostrando 
 solo la cabecera y que se pueda ampliar para ver el contenido pulsando 
 en el típico "+".
 
* (Daniel) [**Dificultad baja**] [**INTERESANTE**] [**Tarea para Iván PR #43**]
Añadir tanto primer alumno en resolver ejercicio, como el segundo y tercero, como si fuera un podio.   

* (Enrique) [**Dificultad media**] [**Tarea para Iván PR #52**]
Permitir varias BD iniciales como casos de prueba en los ejercicios (actualmente solo se considera una BD inicial). 


 
## Daniel

 * (Daniel) [**Dificultad baja**] [**Tarea para Daniel 11/11/2020-28/02/2021 PR #33**]
Subir solución como fichero SQL arrastrando o con botón.

* (Enrique) [**Dificultad baja**] [**INTERESANTE**] [**Tarea para Daniel PR #47**]
Mejorar la salida esperada en los ejercicios de procedimientos.
Ahora mismo muestra todas las tablas que existen en la base de 
datos después de invocar al procedimiento, pero sería mejor que
mostrase únicamente las que han cambiado: tabla eliminada, tabla 
nueva, tabla que tiene filas diferentes (añadidas, borradas o 
modificadas).

* (Daniel) [**Dificultad media**] [**INTERESANTE**] [**Tarea para Daniel PR #49**]
Sistema de logros para aumentar la competitividad, p-ej. `Realiza 3 ejercicios de inserción`

* (Jesús) [**Dificultad alta**] [**Tarea para Daniel PR #63 y PR #64**]
Diseñar los conjuntos de datos necesarios para probar una consulta que es errónea. Otro enfoque (Enrique) sería dar dos consultas SQL y pedir al estudiante qué datos tendrían que tener las tablas para que los resultados fueran diferentes.
  
* (Daniel) [**Dificultad baja**] [**Tarea para Daniel PR #70**]
Añadir dos nuevas definiciones de logros.



## Tamara 
 
* (Tamara) [**Dificultad baja**] [**IMPRESCINDIBLE**] [**Tarea para Tamara 28/10 PR #28**]
En el apartado "Mis envíos" añadir un botón para descargar el código enviado de un ejercicio.

* (Enrique y Jesús) [**Dificultad baja**] [INTERESANTE] [**Tarea para Tamara PR #48**]
  Descargar el listado de envíos de la pestaña 'Resultados'



# Tareas asignadas:

* (Jesús) [**Dificultad alta**] [IMPRESCINDIBLE] [**Tarea para Iván**]
 Soporte multi-idioma para mostrar el sistema en inglés y (Daniel) otros idiomas incluidos los demás de España como el valenciano. (https://docs.djangoproject.com/en/3.1/topics/i18n/)
 
* (Tamara e Iker) [**Dificultad alta**] [**INTERESANTE**] [**Tarea para Tamara**]
    * Opción de pista en cada ejercicio para los alumnos que no sepan empezar un ejercicio. En el caso de tener un sistema de puntos se les restaría un porcentaje por cada ejercicio en el que han necesitado ayuda.
    * Cada alumno tiene una serie de "saldo" el cual recibe tras un aceptado, logros (subir tres seguidos bien, alguno por dificultad tener más premio), que los comentarios de ayuda aparezca un botoncito con un máximo de 3 ayudas y cada vez más caros (3 , 5 , 10 por ejemplo) y sean ayudas genéricas para cada ejercicio.

* [**Dificultad media**] [**Tarea para Tamara**]
Indicar al usuario en el momento que ha obtenido un logro, en cuanto realiza un envío.


# Tareas propuestas:

* (Jesús) [**Dificultad alta**] [INTERESANTE]
 Triggers: mejorar la comparación de resultados y diseño de casos de prueba.

* (Jesús y Enrique) 
     * [**Dificultad baja**] [**INTERESANTE**] Permitir que cada problema tenga una puntuación diferente y que esos
       puntos generen la clasificación. Mostrar primer estudiante en resolver cada problema y generar un reporte (idealmente Moodle)
     * [**Dificultad alta**] [**INTERESANTE**] Modo examen: horario reducido, sin retroalimentación de solución o sin mostrar el resultado esperado. ¿Crear una agrupación concreta para cada examen con usuarios nuevos o reutilizar los existentes?

* (Jesús) [**Dificultad media**] 
 Representación gráfica del diseño de BD de cada pregunta (al estilo del modelo relacional o tipo UML, representando claves externas y primarias, etc.). 
  
* (Jesús)[**Dificultad alta**]
 Mejorar retroalimentación: pistas más inteligentes, p.ej. `Te falta usar la tabla X en FROM`

* (Enrique) [**Dificultad alta**]
Soporte de otros SGBD: PostgreSQL, MySQL, MariaDB, SQLite, etc.

* (Jesús) [**Dificultad media**] [**INTERESANTE**]
Comprobar también la salida estándar en PL/SQL (PUT_LINE)

* (Jesús) [**Dificultad media**] [**INTERESANTE**]
Gestión de excepciones en PL/SQL: ver que se lanzan las que deberían

* (Jesús) [**Dificultad media**]
Permitir varios casos de prueba en PL/SQL con distintos valores para los parámetros (actualmente suportado en funciones pero no en procedimientos).

* (Daniel) [**Dificultad alta**] [**INTERESANTE**]
Corrección diciendo si está algo 'medio bien', como refuerzo a las pistas.

* (Daniel) [**Dificultad alta**] [**INTERESANTE**]
Sistema de comunicación con el profesor para resolver dudas de ejercicios específicos.

* (Daniel) [**Dificultad media**] [**INTERESANTE**]
Función para que el alumno pueda agregar algún caso de prueba específico => solo relativo a `INSERT VALUE`.
Enrique: ojo a posibles problemas de injección.

* (Jesús) [**Dificultad media**] [**INTERESANTE**]
Añadir una opción que permita introducir en formato "libre" (como
SQLDeveloper, o https://livesql.oracle.com/) instrucciones a ejecutar
en un esquema limpio de BD. Los esquemas generados de esta forma deben
permitir un nivel de persistencia asociado al usuario, por ejemplo
hasta las 00:00 del día siguiente. O mejor aún, que se pueda
configurar para cada usuario.