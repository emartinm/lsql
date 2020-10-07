# TODO:
 * Hacer un robots.txt para evitar que indexen imágenes ni nada
 * Indicar ilustraciones obtenidas de:
   * https://freesvg.org/red-cross-not-ok-vector-icon (dominio público)
   * https://icons.getbootstrap.com/ (MIT)
 
# Mejoras propuestas:
 * (Jesús) [**Dificultad alta**] 
 Soporte multi-idioma para mostrar el sistema en inglés y (Daniel) otros idiomas incluidos los demás de España como el valenciano. (https://docs.djangoproject.com/en/3.1/topics/i18n/)

 * (Jesús) [**Dificultad baja**] 
 Botón para descargarse el *script* de creación de las tablas y carga de datos en cada problema.

 * (Jesús) [**Dificultad alta**] 
 Triggers: mejorar la comparación de resultados y diseño de casos de prueba.

 * (Jesús) [**Dificultad media**] 
 Almacenar puntuación para calificar automáticamente algunos ejercicios (exportar o comunicar con Moodle), gestión de grupos de clase, etc.

 * (Jesús) [**Dificultad media**] 
 Representación gráfica del diseño de BD de cada pregunta (al estilo del modelo relacional o tipo UML, representando claves externas y primarias, etc.). Otra idea (Enrique) es mostrar al menos las tablas de manera más compacta, p.ej. mostrando solo la cabecera y que se pueda ampliar para ver el contenido pulsando en el típico "+".

 * (Jesús) [**Dificultad media**] 
 Modo competición: ver los resultados de los demás estudiantes y sus puntos, primer estudiante en resolver cada problema. ¿Agrupar por clases/ver todos?

*  (Jesús) [**Dificultad alta**] 
Modo examen: horario reducido, sin retroalimentación de solución o sin mostrar el resultado esperado. ¿Crear una agrupación concreta para cada examen con usuarios nuevos o reutilizar los existentes?

* (Jesús)[**Dificultad alta**] 
 Mejorar retroalimentación: pistas más inteligentes, p.ej. `Te falta usar la tabla X en FROM`

* (Enrique) [**Dificultad alta**] 
Soporte de otros SGBD: PostgreSQL, MySQL, MariaDB, SQLite, etc.

* (Jesús) [**Dificultad media**] 
Comprobar también la salida estándar en PL/SQL (PUT_LINE)

* (Jesús) [**Dificultad media**] 
Gestión de excepciones en PL/SQL: ver que se lanzan las que deberían

* (Jesús) [**Dificultad media**] 
Permitir varios casos de prueba en PL/SQL con distintos valores para los parámetros (actualmente suportado en funciones pero no en procedimientos).

* (Enrique) [**Dificultad media**] 
Permitir varias BD iniciales como casos de prueba en los ejercicios (actualmente solo se considera una BD inicial).

* (Daniel) [**Dificultad baja**] 
Subir solución como fichero SQL arrastrando o con botón.

* (Jesús) [**Dificultad alta**] 
Diseñar los conjuntos de datos necesarios para probar una consulta que puede ser errónea. Otra enfoque (Enrique) sería dar dos consultas SQL y pedir al estudiante qué datos tendrían que tener las tablas para que los resultados fueran diferentes.

* (Daniel) [**Dificultad media**] 
Sistema de logros para aumentar la competitividad, p-ej. `Realiza 3 ejercicios de inserción`

* (Daniel) [**Dificultad alta**] 
Corrección diciendo si está algo 'medio bien', como refuerzo a las pistas.

* (Daniel) [**Dificultad baja**] 
Añadir tanto primer alumno en resolver ejercicio, como el segundo y tercero, como si fuera un podio.

* (Daniel) [**Dificultad alta**] 
Sistema de comunicación con el profesor para resolver dudas de ejercicios específicos.

* (Daniel) [**Dificultad media**] 
Función para que el alumno pueda agregar algún caso de prueba específico.
Enrique: ojo a posibles problemas de injección si se hace disponible para todos.

* (Tamara) [**Dificultad baja**] 
En el apartado "Mis envíos" añadir un botón para descargar el código enviado de un ejercicio.

* (Tamara) [**Dificultad media**] 
Opción de pista en cada ejercicio para los alumnos que no sepan empezar un ejercicio. En el caso de tener un sistema de puntos se les restaría un porcentaje por cada ejercicio en el que han necesitado ayuda.

* (Iker) [**Dificultad a determinar**] 
Cada alumno tiene una serie de "saldo" el cual recibe tras un aceptado, logros (subir tres seguidos bien, alguno por dificultad tener más premio), que los comentarios de ayuda aparezca un botoncito con un máximo de 3 ayudas y cada vez más caros (3 , 5 , 10 por ejemplo) y sean ayudas genéricas para cada ejercicio.
