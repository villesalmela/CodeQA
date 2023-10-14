// A helper function to convert strings to numbers and "None" to null.
function convert(str) {

    // Handle "None"
    if (str === "None") {
        return null;
    }

    // Cast string to number
    let num = Number(str);

    // Account for null indexing
    return num - 1;
}

// Variable to hold markers
var marker_dict = {};

// Remove highlight
function unhighlightError(editor, key) {
    editor.getSession().removeMarker(marker_dict[key]);
}

// Add highlight
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

    marker_key = 1
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

// sets a spinner on top a form, which is displayed after the form is submitted, until page reloads
function setSpinner(form_id) {
    
    // insert the overlay
    var div_content = `
        <div class="overlay" id="loadingOverlay">
            <div class="spinner" id="spinner">
            Loading...
            </div>
        </div>
        `;
    jQuery(form_id).before(div_content);

    // add event listener
    const form = document.getElementById(form_id);
    form.addEventListener('submit', function () {
        
        // get the form dimensions
        const rect = form.getBoundingClientRect();
        
        // set the overlay to match dimensions
        const overlay = document.getElementById("loadingOverlay");
        overlay.style.width = rect.width + "px";
        overlay.style.height = rect.height  + "px";
        overlay.style.top = rect.top + "px";
        overlay.style.left = rect.left + "px";

        // display the overlay
        overlay.style.display = "block";
        
        // display the spinner
        document.getElementById("spinner").style.display = "block";
    });
}


// function for adding new editor
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
    if (annotations != null) {
        editor.setReadOnly(true);
        editor.session.setAnnotations(annotations);
    }
    if (target_field != null) {
        // add editor content to form when it is submitted
        document.querySelector('form').addEventListener('submit', function () {
            document.getElementById(target_field).value = editor.getValue();
        });
    }
}

// function for adding row-click handler
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

// function for converting normal html table to jQuery Datatable
function makeDatatable(table_id) {
    jQuery(document).ready(function () {
        var $table = jQuery('#' + table_id)
        $table.DataTable({
            hover: true
        });
        $table.addClass("hover")
    });
}

function rating(function_id, defaultValue) {
    jQuery(document).ready(function(){

        // set default value
        jQuery("input:radio[name='rating'][value='" + defaultValue + "']").prop('checked', true);

        // listen for changes
        jQuery("input:radio[name='rating']").change(function(){
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
            success: function(response) {
                var newAverage = response.average
                jQuery("#average-rating").attr("data-rating", newAverage.toString())
            },
            
            // reset to default rating if saving fails
            error: function() {
              alert("Failed to save rating");
              jQuery("input:radio[name='rating'][value='" + defaultValue + "']").prop('checked', true);
            }
          });
        });
      });
}