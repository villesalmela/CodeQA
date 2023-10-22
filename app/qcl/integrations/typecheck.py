import json
import subprocess


def run_pyright(filename) -> list[dict[str, str]]:
    "Run pyright type-checking against a given file"

    command = ["pyright", "--warnings", "--outputjson", filename]
    result = subprocess.run(command, capture_output=True, text=True, check=False)

    if result.returncode == 0:
        return []
    else:
        output_json = json.loads(result.stdout)
        diags = output_json["generalDiagnostics"]
        out = []
        for diag in diags:
            issue = {}
            issue["severity"] = diag["severity"]
            issue["message"] = diag["message"]
            issue["line"] = diag["range"]["start"]["line"] + 1
            issue["endLine"] = diag["range"]["end"]["line"] + 1
            issue["col"] = diag["range"]["start"]["character"]
            issue["endCol"] = diag["range"]["end"]["character"]
            out.append(issue)
    return out
