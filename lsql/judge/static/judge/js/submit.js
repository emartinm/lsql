const auth_msg = 'Ha habido un error de autenticación al conectar con el corrector de ejercicios. ' +
                 'Por favor, vuelve a cargar la página del problema e intenta ' +
                 'enviarlo de nuevo dentro de unos instantes.';
const correction_error = 'Ha sido imposible conectar con el corrector de ejercicios. ' +
                         'Este problema puede ser debido a una saturación del servidor. ' +
                         'Por favor, vuelve a cargar la página del problema e intenta ' +
                         'enviarlo de nuevo dentro de unos instantes. Ponte en contacto con tu ' +
                         'profesor si el problema persiste.';

function show_modal(titulo, contenido, botonVerde) {
    $('#tituloCorreccion').text(titulo);
    $('#mensajeCorreccion').text(contenido);
    $('#ventanaResultado').modal();
    if (botonVerde) {
        $('#botonCerrarModal').attr('class', 'btn btn-success');
    } else {
        $('#botonCerrarModal').attr('class', 'btn btn-danger');
    }
    // Reloads highlight.js to format new code in feedback
    hljs.initHighlighting.called = false;
    hljs.initHighlighting();top

}

function mark_solved() {
    $('#markSolved').css("visibility", "visible");
}

function update_page_submission_in_progress() {
    $('#botonEnviar').attr('disabled', true);
    //$('#codigo').attr('disabled', true);
    ace.edit("codigo").setReadOnly(true);
    $('#spinnerEnviar').removeAttr("hidden");
    $('#textoBotonEnviar').text("Enviando...");
}

function update_page_submission_received() {
    $('#botonEnviar').removeAttr("disabled");
    //$('#codigo').removeAttr("disabled");
    ace.edit("codigo").setReadOnly(false);
    $('#spinnerEnviar').attr('hidden', true);
    $('#textoBotonEnviar').text("Enviar solución");
}

function show_feedback(html) {
    $('#results_box').removeAttr("hidden");
    $('#feedback_content').empty();
    $('#feedback_content')[0].insertAdjacentHTML('beforeend', html);
}

function hide_feedback() {
    $('#results_box').attr('hidden', true);
}

function send_solution() {
    let endpoint = $('#endpoint').val();
    var formData = new FormData();
    update_page_submission_in_progress();
    // Extracts code from ACE editor
    let code = ace.edit("codigo").getValue();
    formData.append('codigo', code);

    const config = {
        method: 'POST',
        mode: 'same-origin', // no-cors, *cors, same-origin
        cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
        credentials: 'same-origin', // include, *same-origin, omit
        headers: { 'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val() },
        redirect: 'follow', // manual, *follow, error
        referrerPolicy: 'same-origin', // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
        body: formData // body data type must match "Content-Type" header
    };
    fetch(endpoint, config)
      .then(function(response) {
          if (response.ok) {
              return response.json();
              // Returns a new Promise, that can be chained
          } else if (response.status == 400 ) {
              throw auth_msg;
          } else {
              throw correction_error;
          }
      })
      .then(function(myJson) {
          // AC = 1, TLE = 2, RE = 3, WA = 4, INTERNAL_ERROR = 5, VALIDATION_ERROR = 6
          console.log(myJson);
          if (myJson.estado == 1) {
              // AC
              const msg = '¡Enhorabuena! Tu código SQL ha generado los resultados esperados.';
              mark_solved();
              hide_feedback();
              show_modal('Aceptado', msg, true);
          } else if (myJson.estado == 2) {
              // TLE
              const msg = 'Puede deberse a una sobrecarga puntual del servidor, pero seguramente sea debido a que tu ' +
                          'código SQL no es suficientemente eficiente. Vuelve a enviarlo en unos minutos y si sigues ' +
                          'obteniendo el mismo veredicto trata de reescribir tu código lo para ser más eficiente.'
              show_feedback(myJson.mensaje);
              show_modal('Tu código ha tardado demasiado en ejecutarse', msg, false);
              hide_feedback();
          } else if (myJson.estado == 3) {
              // RE
              const msg = 'Tu código SQL ha producido un error durante la ejecución. Consulta el cuadro rojo en ' +
                          'la parte inferior de la página para ver los detalles.';
              show_feedback(myJson.mensaje);
              show_modal('Error de ejecución', msg, false);
          } else if (myJson.estado == 4) {
              // WA
              const msg = 'Tu código SQL ha generado resultados erróneos. Consulta el cuadro rojo en ' +
                          'la parte inferior de la página para ver los detalles.';
              show_feedback(myJson.mensaje);
              show_modal('Respuesta incorrecta', msg, false);
          } else if (myJson.estado == 6) {
              hide_feedback();
              show_modal('Error de validación de tu código SQL', myJson.mensaje, false);
          } else { // INTERNAL_ERROR or incorrect code
              hide_feedback();
              const msg = 'Error inesperado al ejecutar tu código. Por favor, inténtalo de nuevo.';
              show_modal('Error inesperado', msg, false);
          }
          update_page_submission_received();
      }).catch(function(e) {
          show_modal('Error de conexión', e, false);
          update_page_submission_received();
      });
}
