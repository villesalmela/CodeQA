import os
from email_validator import validate_email, EmailNotValidError
from wtforms.validators import ValidationError


ALLOWED_DOMAINS = [x.strip() for x in os.environ["ALLOWED_DOMAINS"].split(",")]


def check_email(form, field) -> None:
    "Custom validator that works with WTForms"

    domain_ok = False
    try:
        emailinfo = validate_email(field.data, check_deliverability=False)
        if emailinfo.domain in ALLOWED_DOMAINS:
            domain_ok = True
        message = ""

    except EmailNotValidError as e:
        message = str(e)
    if not domain_ok:
        message += (
            " The application is in private preview, email domain restrictions apply."
        )
    if message:
        raise ValidationError(message)
