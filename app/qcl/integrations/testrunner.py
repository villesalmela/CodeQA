import json
import os
import boto3


# Load keys
lambda_pytest_key_id = os.environ.get("PYTEST_KEY_ID")
lambda_pytest_key_secret = os.environ.get("PYTEST_KEY_SECRET")
lambda_pytest_region = os.environ.get("PYTEST_REGION")

# Initialize a session
session = boto3.Session(
    aws_access_key_id=lambda_pytest_key_id,
    aws_secret_access_key=lambda_pytest_key_secret,
    region_name=lambda_pytest_region,
)

# Initialize Lambda client using the session
lambda_client = session.client("lambda")


def execute(func: str, test: str) -> dict:
    "Run the unit tests against the given function, using AWS lambda"

    data = json.dumps({"func": func, "test": test})
    response = lambda_client.invoke(
        FunctionName="pytest",
        InvocationType="RequestResponse",
        Payload=bytes(data, encoding="utf-8"),
    )
    status = response["StatusCode"]
    error = response.get("FunctionError")
    payload = response["Payload"].read().decode("utf-8")
    if status == 200 and not error:
        out = json.loads(payload)
    else:
        out = {"error": error, "payload": json.loads(payload)}
    return out


def handle(result: dict) -> tuple:
    "Handle results from the lambda function."

    if "error" in result:
        if "Task timed out after" in result.get("errorMessage", ""):
            return False, {
                "executed": 0,
                "errors": [
                    f"{result['error']}: Execution took too long, task timed out."
                ],
            }
        elif "errorType" in result["payload"]:
            return False, {
                "executed": 0,
                "errors": [
                    f"{result['error']}: {result['payload']['errorType']}: {result['payload']['errorMessage']}"
                ],
            }
        else:
            return False, {
                "executed": 0,
                "errors": [f"{result['error']}: {result['payload']['errorMessage']}"],
            }
    else:
        success = result["successful"]
        executed = result["total"]
        errors = result["errors"]
        failures = result["failures"]
        skipped = result["skipped"]
        ok = executed - len(errors) - len(failures) - len(skipped)
        return success, {
            "executed": executed,
            "ok": ok,
            "errors": errors,
            "failures": failures,
            "skipped": skipped,
        }
