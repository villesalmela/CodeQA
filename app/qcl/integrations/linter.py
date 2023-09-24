from io import StringIO
from bs4 import BeautifulSoup
from pylint.lint import Run
from pylint.reporters.json_reporter import JSONReporter
import json
import requests

def run_pylint(filename):
    
    # redirect output to temporary stringio object
    pylint_output = StringIO()
    
    # get results in json
    reporter = JSONReporter(pylint_output)
    
    # run pylint
    Run([filename], reporter=reporter, exit=False)
    
    # scroll back to start
    pylint_output.seek(0)
    
    # read the output
    lint_result = json.load(pylint_output)

    # get and parse message descriptions from project website
    base_url = "https://pylint.pycqa.org/en/latest/user_guide/messages/"
    description_cache = {}
    for entry in lint_result:
        if entry["message-id"] not in description_cache:
            url = f"{base_url}/{entry['type']}/{entry['symbol']}.html"
            page = requests.get(url)
            html = page.content
            soup = BeautifulSoup(html, 'html.parser')
            section = soup.find('section', {'id': f'{entry["symbol"]}-{entry["message-id"].lower()}'})

            # Find the <p> element where the description is
            p_tag = section.find('p', string='Description:').find_next_sibling()

            # Extract the text from the <p> element
            text = p_tag.text if p_tag else None
        
            # Use cache to avoid fetching the same description multiple times
            description_cache[entry["message-id"]] = text

        # Add the description to the entry
        entry["description"] = description_cache[entry["message-id"]]

    return lint_result