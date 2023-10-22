import os
from mailjet_rest import Client
from qcl import app

api_key = os.environ.get("MJ_APIKEY_PUBLIC")
api_secret = os.environ.get("MJ_APIKEY_SECRET")
template_id = os.environ.get("MJ_TEMPLATE_ID")
mailjet = Client(auth=(api_key, api_secret), version="v3.1")


def send_verification_code(receiver: str, code: str) -> None:
    "Send verification code via email, using Mailjet API."

    code = code[0:3] + " - " + code[3:6]
    data = {
        "Messages": [
            {
                "To": [{"Email": receiver}],
                "TemplateID": int(template_id),
                "TemplateLanguage": True,
                "Variables": {"VERIFICATION_CODE": code},
            }
        ]
    }

    result = mailjet.send.create(data=data)
    api_status = result.status_code == 200
    app.logger.debug(result.content)
    message_status = result.json()["Messages"][0]["Status"] == "success"
    success = api_status and message_status
    if not success:
        raise RuntimeError(
            f"Failed to send email verification code: {api_status=}, {message_status=}"
        )
