# Funcionalidad por portar
 * Mostrar estadísticas de problemas (solucionados, envios)
 * Mostrar el icono de superacion en listado y en enunciado
 * Mostrar listado de envios
 * Añadir varios problemas de golpe a una coleccion (con un zip, siendo el autor el mismo que el de la colección).
 * Recuperar el log (ahora mismo no muestra nada)

# TODO:
 * Establecer el fichero ZIP a None una vez que se han extraido los datos en Problem y Collection
 * Mostrar el widget de añadir ZIP en Collection únicamente cuando ya existe y tiene col_id.
 * Añadir pruebas automáticas
 * En el repositorio GitHub, añadir comprobaciones (pylint, mypy, cobertura de tests...) => TravisCI?
 * Hacer un robots.txt para evitar que indexen imágenes ni nada
 * Aislar cada parte en su docker:
   * Incluir el frontend dentro de un docker ubuntu:latest personalizado
     que lanza gunicorn. Redirigir puerto al lanzar
   * Usar imagen docker de postgresql 12
   * Usar imagen docker de oracle 11g XE
 * Indicar ilustraciones obtenidas de:
   * https://freesvg.org/red-cross-not-ok-vector-icon (dominio público)
   * https://icons.getbootstrap.com/ (MIT)
 
# Mejoras propuestas:
 * (Jesús Correas) Que se pueda poner en inglés
 * (Jesús Correas) Que en todos los ejercicios haya un botón para descargarse el script de creación de las tablas y carga de datos.
 * (Jesús Correas) Triggers: mejorar la comparación de resultados y diseño de casos de prueba.
 * (Jesús Correas) Incluir almacenar datos de puntuación para calificar automáticamente, gestión de grupos de clase, etc.
 * (Jesús Correas) Hacer una representación gráfica del diseño de BD de cada pregunta (al estilo del modelo relacional o tipo uml, representando claves externas y primarias, etc.)


