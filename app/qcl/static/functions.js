// A helper function to convert strings to numbers and "None" to null.
function convert(str) {

    // handle "None"
    if (str === "None") {
        return null;
    }

    // cast string to number
    let num = Number(str);

    // account for null indexing
    return num - 1;
}

// Dictionary to hold markers that highlight text on code editor
var marker_dict = {};

// Remove highlight in code editor
function unhighlightError(editor, key) {
    editor.getSession().removeMarker(marker_dict[key]);
}

// Add highlight in code editor
function highlightError(editor, key, startline, endline, startcol, endcol) {
    unhighlightError(editor, key);
    var Range = ace.require("ace/range").Range
    marker_dict[key] = editor.session.addMarker(new Range(startline, startcol, endline, endcol), "line-highlight", "text");
}

// This function will highlight the corresponding row on code editor, when item on the linting results table is clicked.
function pylintRowClicked(row) {

    editor_container = document.getElementById("lint_box")
    editor = ace.edit(editor_container)

    // get the relevant cells
    const cells = Array.from(row.cells);

    // extract innerText from cells
    const cellData = cells.map(cell => cell.innerText);

    // extract values from cells
    const startline = convert(cellData[4]);
    var startcol = convert(cellData[5]);
    var endline = convert(cellData[6]);
    var endcol = convert(cellData[7]);

    // set default values
    if (endline === null || endline === undefined) {
        var endline = startline;
    }

    if (endcol === null || endcol === undefined) {
        var endcol = Infinity;
    }

    if (startcol === null || startcol === undefined) {
        var startcol = 1;
    }

    // unique key for each editor
    marker_key = 1

    // apparently null indexing on lines, but not on columns
    highlightError(editor, marker_key, startline, endline, startcol + 1, endcol + 1);
}

// This function will highlight the corresponding row on code editor, when item on the security results table is clicked.
function banditRowClicked(row) {

    editor_container = document.getElementById("security_box")
    editor = ace.edit(editor_container)

    // get the relevant cells
    const cells = Array.from(row.cells);

    // extract innerText from cells
    const cellData = cells.map(cell => cell.innerText);

    // extract values from cells
    const startline = convert(cellData[7]);
    var startcol = convert(cellData[8]);
    var endline = convert(cellData[9]);
    var endcol = convert(cellData[10]);

    // set default values
    if (endline === null || endline === undefined) {
        var endline = startline;
    }

    if (endcol === null || endcol === undefined) {
        var endcol = Infinity;
    }

    if (startcol === null || startcol === undefined) {
        var startcol = 1;
    }

    // unique key for each editor
    marker_key = 2

    // apparently null indexing on lines, but not on columns
    highlightError(editor, marker_key, startline, endline, startcol + 1, endcol + 1);
}

// This function will highlight the corresponding row on code editor, when item on the typechecking results table is clicked.
function pyrightRowClicked(row) {

    editor_container = document.getElementById("type_box")
    editor = ace.edit(editor_container)

    // get the relevant cells
    const cells = Array.from(row.cells);

    // extract innerText from cells
    const cellData = cells.map(cell => cell.innerText);

    // extract values from cells
    const startline = convert(cellData[2]);
    var startcol = convert(cellData[3]);
    var endline = convert(cellData[4]);
    var endcol = convert(cellData[5]);

    // set default values
    if (endline === null || endline === undefined) {
        var endline = startline;
    }

    if (endcol === null || endcol === undefined) {
        var endcol = Infinity;
    }

    if (startcol === null || startcol === undefined) {
        var startcol = 1;
    }

    // unique key for each editor
    marker_key = 3

    // apparently null indexing on lines, but not on columns
    highlightError(editor, marker_key, startline, endline, startcol + 1, endcol + 1);
}

// This function will parse linting results table, and extract messages and relevant code locations
// Output is in a format that can be used to set annotations in Ace editor
function parse_lint_results() {
    const rows = document.querySelectorAll('#lint-results tbody tr');
    const annotations = [];

    rows.forEach(row => {

        // get cell data
        const cells = row.querySelectorAll('td');

        // extract values from cells
        var type = cells[0].innerText;
        const message = cells[2].innerText;
        const startLine = parseInt(cells[4].innerText, 10) - 1;

        // convert to info/warning/error
        if (type == "convention" || type == "information" || type == "refactor") {
            type = "info"
        } else if (type == "fatal" || type == "error") {
            type = "error"
        } else if (type == "warning") {
            type = "warning"
        } else {
            type = "error"
        }

        // build annotation and add it to list
        annotations.push({
            row: startLine,
            column: 0,
            text: message,
            type: type
        });
    });

    return annotations;
}

// This function will parse security results table, and extract messages and relevant code locations
// Output is in a format that can be used to set annotations in Ace editor
function parse_security_results() {
    const rows = document.querySelectorAll('#security-results tbody tr');
    const annotations = [];

    rows.forEach(row => {

        // get cell data
        const cells = row.querySelectorAll('td');

        // extract values from cells
        var severity = cells[3].innerText;
        const message = cells[2].innerText;
        const startLine = parseInt(cells[7].innerText, 10) - 1;

        // convert to info/warning/error
        if (severity == "LOW") {
            type = "info"
        } else if (severity == "MEDIUM") {
            type = "warning"
        } else {
            type = "error"
        }

        // build annotation and add it to list
        annotations.push({
            row: startLine,
            column: 0,
            text: message,
            type: type
        });
    });

    return annotations;
}

// This function will parse typechecking results table, and extract messages and relevant code locations
// Output is in a format that can be used to set annotations in Ace editor
function parse_type_results() {
    const rows = document.querySelectorAll('#type-results tbody tr');
    const annotations = [];

    rows.forEach(row => {

        // get cell data
        const cells = row.querySelectorAll('td');

        // extract values from cells
        var severity = cells[0].innerText;
        const message = cells[1].innerText;
        const startLine = parseInt(cells[2].innerText, 10) - 1;

        // convert to info/warning/error
        if (severity == "information") {
            type = "info"
        } else if (severity == "warning") {
            type = "warning"
        } else {
            type = "error"
        }

        // build annotation and add it to list
        annotations.push({
            row: startLine,
            column: 0,
            text: message,
            type: type
        });
    });

    return annotations;
}

// Function for adding new code editor
function addEditor(editor_id, content, target_field = null, annotations = null) {

    // configure ace
    ace.config.set("useStrictCSP", true);

    // create the editor
    var editor = ace.edit(editor_id);
    editor.setTheme("ace/theme/monokai");
    editor.getSession().setMode("ace/mode/python");
    editor.setValue(content);
    editor.setHighlightActiveLine(false);
    editor.clearSelection()

    // if there are annotations
    if (annotations != null) {

        // prevent edits (which would invalidate annotation's locations)
        editor.setReadOnly(true);

        // and set the annotations
        editor.session.setAnnotations(annotations);
    }

    // if is related to a form
    if (target_field != null) {

        // add editor content to form when it is submitted
        document.getElementById('form').addEventListener('submit', function () {
            document.getElementById(target_field).value = editor.getValue();
        });
    }
}

// Function for adding row-click handler
function addRowHandler(table_id, func) {

    // handle highlighting rows in code, based on user clicking rows on results table
    jQuery(document).ready(function () {

        // the results table
        const table = document.getElementById(table_id);

        // the table
        table.addEventListener("click", function (event) {

            // the row which was clicked
            let row = event.target.closest('tr');

            // run the function
            func(row);
        });
    });
}

// Function for converting normal html table to jQuery Datatable
function makeDatatable(table_id, columns = []) {
    jQuery(document).ready(function () {
        var $table = jQuery('#' + table_id)
        var options = {
            hover: true,
            searching: false,
            lengthChange: false
        }
        if (columns.length > 0) {
            options.columns = columns
        }
        $table.DataTable(options);
        $table.addClass("hover")

    });
}

// Function for handling interaction between frontend and backend components, related to rating functionality
function rating(function_id, defaultValue) {
    jQuery(document).ready(function () {

        // set default value
        jQuery("input:radio[name='rating'][value='" + defaultValue + "']").prop('checked', true);

        // listen for changes
        jQuery("input:radio[name='rating']").change(function () {
            var selected_rating = jQuery(this).val();

            // launch api call when user gives rating
            jQuery.ajax({
                url: '/api/save_rating',
                type: 'POST',
                data: {
                    'rating': selected_rating,
                    'function_id': function_id
                },

                // get new average rating in return
                success: function (response) {
                    var newAverage = response.average
                    jQuery("#average-rating").attr("data-rating", newAverage.toString())
                },

                // reset to default rating if saving fails
                error: function () {
                    alert("Failed to save rating");
                    jQuery("input:radio[name='rating'][value='" + defaultValue + "']").prop('checked', true);
                }
            });
        });
    });
}

// Function for setting a spinner in button, when it's clicked
function setSpinner(formId) {

    // select all buttons within the given form
    const $buttons = $(`#${formId} .btn`);
    console.log($buttons)

    // attach listener to each button
    $buttons.on("click", function () {

        // add spinner button next to it, then hide the original, effectively swapping them
        var content = `<button type="button" class="btn btn-outline-light"><span class="spinner-border spinner-border-sm"></span>Loading...</button>`
        $(this).attr("value", "Loading...")
            .before(content)
            .hide();
    });
}