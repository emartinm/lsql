/**********************************************************
 * Copyright Enrique Martín Martín <emartinm@ucm.es> 2020 *
 **********************************************************/


// Shows a modal window with a title and message
function show_modal(title, message, achievements) {
    $('#modal_title').text(title);
    $('#modal_message').text(message);
    var html = $.parseHTML(achievements);
    $('#achieve_sentence').replaceWith(html);
    $('#result_window').modal("show")
    // Reloads highlight.js to format new code in feedback
    hljs.initHighlighting.called = false;
    hljs.initHighlighting();
}

// Shows a modal windows with a connection error message
function show_error_modal() {
     $('#error_window').modal("show");
}

// Shows the 'solved' mark next to the problem title
function mark_solved(myJson) {
    if (myJson.veredict == "AC")
        $('#check-icon').removeClass("icon-hidden");
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

// Selects in the editor the fragment of SQL code that generates a problem if offset if provided
function select_error_in_editor(myJson) {
    if (myJson.position) {
        let line = myJson.position[0];
        let col = myJson.position[1];
        ace.edit('user_code').selection.moveCursorTo(line, col, false);
        ace.edit('user_code').selection.selectAWord();
        $('#feedback_line').removeAttr('hidden');
        $('#feedback_line').text(myJson.position_msg);
    } else {
        $('#feedback_line').attr('hidden', true);
    }
}

// Submits the solution and receives and shows the verdict
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
          select_error_in_editor(myJson);
          show_modal(myJson.title, myJson.message, myJson.achievements);
          update_page_submission_received();
      }).catch(function(e) {
          console.log(e);
          show_error_modal();
          update_page_submission_received();
      });
}

function load_submission_code(event){
    var input = event.target;

    var reader = new FileReader();
    reader.onload = function(){
        var text = reader.result;
        ace.edit('user_code').setValue(reader.result);
        ace.edit('user_code').selection.clearSelection();
    };
    reader.readAsText(input.files[0]);
}

// disable the button if no more available hints
function disable_button_ask_hint(){
    $('#button_ask_hint').attr('disabled', true);
}

function hide_hint_message(){
    $('#msg').attr('style', 'display: none');
}

function show_hint_message(msg){
    $('#msg').attr('style', '');
    $('#msg_info').text(msg);
}

// show the requested hint or a message with information
function show_hint(){
    // Get json with the hints
    let hint_point = $('#hint_url').val();

    const config = {
        method: 'POST',
        mode: 'same-origin', // no-cors, *cors, same-origin
        cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
        credentials: 'same-origin', // include, *same-origin, omit
        headers: { 'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val() }, // CSRF token from form
        redirect: 'follow', // manual, *follow, error
        referrerPolicy: 'same-origin' // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
    };

    fetch(hint_point, config)
        .then(function(response) {
            if (response.ok) {
                return response.json(); // Returns a new Promise, that can be chained
            } else {
                throw response;
            }
        })
        .then(function(myJson) {

            var hint = myJson['hint'];
            var msg = myJson['msg'];
            var more_hints = myJson['more_hints']
            console.log(myJson);

            if (hint.length > 0){
                $('#info_hint').append(hint);
                hide_hint_message();
            }

            if (msg.length > 0){
               show_hint_message(msg);
            }else{
                hide_hint_message();
            }

            if(!more_hints){
                show_hint_message(msg);
                disable_button_ask_hint();
            }
        });
}
