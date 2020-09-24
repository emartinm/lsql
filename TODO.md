# TODO:
 * Hacer un robots.txt para evitar que indexen imágenes ni nada
 * Indicar ilustraciones obtenidas de:
   * https://freesvg.org/red-cross-not-ok-vector-icon (dominio público)
   * https://icons.getbootstrap.com/ (MIT)
 
# Mejoras propuestas:
 * (JC) Soporte multi-idioma para mostrar el sistema en inglés (https://docs.djangoproject.com/en/3.1/topics/i18n/)
 * (JC) Botón para descargarse el *script* de creación de las tablas y carga de datos en cada problema.
 * (JC) Triggers: mejorar la comparación de resultados y diseño de casos de prueba.
 * (JC) Almacenar puntuación para calificar automáticamente algunos ejercicios (exportar o comunicar con Moodle), 
 gestión de grupos de clase, etc.
 * (JC) Representación gráfica del diseño de BD de cada pregunta (al estilo del modelo relacional o tipo UML, 
 representando claves externas y primarias, etc.)
 * (JC) Modo competición: ver los resultados de los demás estudiantes y sus puntos, primer estudiante en resolver cada 
 problema. ¿Agrupar por clases/ver todos?
*  (JC) Modo examen: horario reducido, sin retroalimentación de solución o sin mostrar el resultado esperado. ¿Crear 
una agrupación concreta para cada examen con usuarios nuevos o reutilizar los existentes?
* (JC) Mejorar retroalimentación: pistas más inteligentes, p.ej. ```Te falta usar la tabla X en FROM```
* (EM) Soporte de otros SGBD: PostgreSQL, MySQL, MariaDB, SQLite, etc.
* (JC) Comprobar también la salida estándar en PL/SQL (PUT_LINE)
* (JC) Gestión de excepciones en PL/SQL: ver que se lanzan las que deberían
* (JC) Permitir varios casos de prueba en PL/SQL con distintos valores para los parámetros (actualmente suportado 
en funciones pero no en procedimientos).
* (EM) Permitir varias BD uniciales como casos de prueba en los ejercicios (actualmente solo se considera una 
BD inicial).
* (DI) Subir solución como fichero SQL arrastrando o con botón.
* (JC) Diseñar los conjuntos de datos necesarios para probar una consulta que puede ser errónea.
* (DI) Traducción a otros idiomas de España como el valenciano.
* (DI) Sistema de logros para aumentar la competitividad, p-ej. ```Realiza 3 ejercicios de inserción```
* (DI) Corrección diciendo si está algo 'medio bien', como refuerzo a las pistas.
* (DI) Añadir tanto primer alumno en resolver ejercicio, como el segundo y tercero, como si fuera un podio.
* (DI) Sistema de comunicación con el profesor para resolver dudas de ejercicios específicos.
* (DI) Función para que el alumno pueda agregar algún caso de prueba específico.


