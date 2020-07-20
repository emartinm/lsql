# TODO:
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


