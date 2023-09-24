// A helper function to convert strings to numbers and "None" to null.
function convert(str) {
    
    // Handle "None"
    if (str === "None") {
        return null;
    }

    // Cast string to number
    let num = Number(str);

    // Row numbers dont start from 0, like indexes do
    return num - 1;
}

// This function will highlight the corresponding row on code editor, when item on the linting results table is clicked.
function pylintRowClicked(row) {

    // First clear all existing highlights
    const elements = document.querySelectorAll('.line-highlight');
    elements.forEach(element => {
        element.classList.remove('line-highlight');
    });

    // Get the relevant cells
    const cells = Array.from(row.cells);
    
    // Get the data inside cells
    const cellData = cells.map(cell => cell.innerText);
    
    // Get start and end linenumbers
    const start = convert(cellData[4])
    const end = convert(cellData[5])

    // If the end is "None", dont do any looping
    if (end === null || end === undefined) {
        
        // Add highlighting to selected row
        editor_for_code.addLineClass(start, 'background', 'line-highlight');
        
        // Exit early
        return;
    }

    // If there is both start and end, go through all lines in between
    for (let i = start; i <= end; i++) {
        
        // Add highlighting to selected row
        editor_for_code.addLineClass(i, 'background', 'line-highlight');
    }

}