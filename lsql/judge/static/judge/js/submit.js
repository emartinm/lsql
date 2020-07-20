/**********************************************************
 * Copyright Enrique Martín Martín <emartinm@ucm.es> 2020 *
 **********************************************************/


// Shows a modal window with a title and message
function show_modal(title, message) {
    $('#modal_title').text(title);
    $('#modal_message').text(message);
    $('#result_window').modal();
    // Reloads highlight.js to format new code in feedback
    hljs.initHighlighting.called = false;
    hljs.initHighlighting();
}

// Shows a modal windows with a connection error message
function show_error_modal() {
     $('#error_window').modal();
}

// Shows the 'solved' mark next to the problem title
function mark_solved(myJson) {
    if (myJson.veredict == "AC")
        $('#markSolved').css('visibility', 'visible');
}

// Disables the form and shows the spinner
function update_page_submission_in_progress() {
    $('#submit_button').attr('disabled', true);
    ace.edit('user_code').setReadOnly(true);
    $('#spinner_submit').removeAttr('hidden');
}

// Enables the form and hides the spinner
function update_page_submission_received() {
    $('#submit_button').removeAttr('disabled');
    ace.edit('user_code').setReadOnly(false);
    $('#spinner_submit').attr('hidden', true);
}

// Shows the feedback in page. If feedback is empty, hides the feedback area
function show_feedback(html) {
    if (html.length > 0) {
        $('#results_box').removeAttr('hidden');
        $('#feedback_content').empty();
        $('#feedback_content')[0].insertAdjacentHTML('beforeend', html);
    } else {
        $('#results_box').attr('hidden', true);
    }
}

// Submits the solution and receives and shows the veredict
function send_solution() {
    // Get endpoint from the form
    let endpoint = $('#endpoint').val();
    update_page_submission_in_progress();

    var formData = new FormData();
    // Extracts code from ACE editor
    let code = ace.edit('user_code').getValue();
    formData.append('code', code);

    const config = {
        method: 'POST',
        mode: 'same-origin', // no-cors, *cors, same-origin
        cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
        credentials: 'same-origin', // include, *same-origin, omit
        headers: { 'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val() }, // CSRF token from form
        redirect: 'follow', // manual, *follow, error
        referrerPolicy: 'same-origin', // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
        body: formData // body data type must match 'Content-Type' header
    };
    fetch(endpoint, config)
      .then(function(response) {
          if (response.ok) {
              return response.json(); // Returns a new Promise, that can be chained
          } else {
              throw response;
          }
      })
      .then(function(myJson) {
          console.log(myJson);
          mark_solved(myJson);
          show_feedback(myJson.feedback);
          show_modal(myJson.title, myJson.message);
          update_page_submission_received();
      }).catch(function(e) {
          console.log(e);
          show_error_modal();
          update_page_submission_received();
      });
}
