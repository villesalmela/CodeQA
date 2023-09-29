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

// Variable to hold linting marker
var marker_lint;

// Remove highlight
function unhighlightError() {
    lint_obj.getSession().removeMarker(marker_lint);
}

// Add highlight
function highlightError(startline, endline, startcol, endcol) {
    unhighlightError();
    var Range = ace.require("ace/range").Range
    marker_lint = lint_obj.session.addMarker(new Range(startline, startcol, endline, endcol), "line-highlight", "text");
}

// This function will highlight the corresponding row on code editor, when item on the linting results table is clicked.
function pylintRowClicked(row) {

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

    // apparently null indexing on lines, but not on columns
    highlightError(startline, endline, startcol + 1, endcol + 1);
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