# Mejoras y extensiones propuestas:

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
  
# Ideas surgidas en el taller de LearnSQL (19 de mayo de 2021)
* Realizar una medida de la complejidad de la consulta enviada por el usuario. 
  En general esto puede ser complejo, pero se podría usar una métrica sencilla como
  que no utiliza tablas innecesarias de acuerdo con la solución oficial.
* Como el usuario ve la base de datos y el resultado esperado, se puede *cablear*
  una consulta que devuelva los datos adecuados sin reunir tablas ni realizar 
  `GROUP BY` o similar. Se podría definir un conjunto de comprobaciones personalizables
  a realizar en el envío del usuario. Debería ser sencillo de configurar por parte del 
  profesor y mostrarse a los alumnos para que sepan desde el principio los requisitos 
  a cumplir:
   1. La consulta involucra las tablas necesarias
   1. Debe contener `GROUP BY`, `ORDER BY`, una consulta anidada, una operación `EXCEPT`,
      etc.
   1. La consulta no puede tener expresiones en la selección de columnas
* Los mensajes de Oracle son muy poco informativos. Estudiar con Fernando Sáenz la
  posibilidad de utilizar analizadores más potentes como los que usa DES para mejorar
  los mensajes de error.

# Otras ideas que pueden ser interesantes (Jesús)
* Crear un modo "examen" que restrinja el acceso a determinados ejercicios, pistas, etc. 
  y que se puedan asignar pesos a los ejercicios que formen el examen para obtener una
  calificación automática. Habilitar un campo para que el profesor pueda introducir una 
  calificación manual para obtener la calificación final.
* Establecer criterios para evitar que el alumno pueda introducir consultas falsas que 
  resuelven el problema con la BD inicial pero no son correctas para otras BD (está 
  relacionado con problemas discriminantes, pero no es lo mismo). Por ejemplo, si la 
  respuesta a un problema es una sola fila con "1", evitar soluciones del tipo "SELECT 1 
  FROM DUAL". Generalizar esto para poder comprobar que un problema se resuelve de 
  determinada forma (por ejemplo, con consultas anidadas, o con reuniones externas,
  etc.).
* Poder añadir referencias (o enlaces) a material docente (transparencias, capítulos de 
  libro, sitios web). Que se puedan añadir en el enunciado del problema o en pistas. Se 
  podría incluir el pdf del material del curso como parte del enunciado del problema.
* Añadir en los problemas sugerencias de otros problemas que se recomienda hacer antes
  o después de ese problema. También problemas relacionados.
