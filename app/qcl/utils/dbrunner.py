from qcl import app, db
from sqlalchemy.sql import text
from sqlalchemy.engine import Result
import traceback
import logging
logging.basicConfig(level=logging.INFO)


def execute(query: str, params: dict[str, str|int|bool]={}) -> tuple[bool, Result|str]:
    logging.info(f"Executing query: '{query}' with params {params}")
    try:

        with app.app_context():
            if params:
                result = db.session.execute(text(query), params)
            else:
                result = db.session.execute(text(query))

            db.session.commit()
        success = True

    except:
        success = False
        result = traceback.format_exc()
        logging.error(result)

    return success, result
