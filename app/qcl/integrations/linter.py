from io import StringIO
import json
from pylint.lint import Run
from pylint.reporters.json_reporter import JSONReporter


def run_pylint(filename):
    "Run pylint against a given file"

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

    # add link to the entry
    base_url = "https://pylint.pycqa.org/en/latest/user_guide/messages"
    for entry in lint_result:
        url = f"{base_url}/{entry['type']}/{entry['symbol']}.html"
        entry["link"] = url

    return lint_result
