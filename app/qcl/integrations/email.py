from mailjet_rest import Client
import os
import traceback

import logging
logging.basicConfig(level=logging.INFO)

api_key = os.environ.get('MJ_APIKEY_PUBLIC')
api_secret = os.environ.get('MJ_APIKEY_SECRET')
template_id = os.environ.get('MJ_TEMPLATE_ID')
mailjet = Client(auth=(api_key, api_secret), version='v3.1')

def send_verification_code(receiver: str, code: str) -> bool:
    code = code[0:3] + " - " + code[3:6]
    data = {
    'Messages': [
            {
                "To": [
                    {
                        "Email": receiver
                    }
                ],
                "TemplateID": template_id,
                "TemplateLanguage": True,
                "Variables": {
                    "VERIFICATION_CODE": code
                }
            }
        ]
    }


    try:
        result = mailjet.send.create(data=data)
        api_status = result.status_code == 200
        logging.info(result.content)
        message_status = result.json()["Messages"][0]["Status"] == "success"
        success = api_status and message_status
    except:
        success = False
        logging.error(traceback.format_exc())

    return success