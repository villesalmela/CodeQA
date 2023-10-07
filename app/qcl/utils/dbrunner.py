from qcl import app, db
from sqlalchemy.sql import text
from sqlalchemy.engine import Result

def execute(query: str, params: dict[str, str|int|bool]={}) -> Result:
    app.logger.debug(f"Executing query: '{query}' with params {params}")

    with app.app_context():
        if params:
            result = db.session.execute(text(query), params)
        else:
            result = db.session.execute(text(query))

        db.session.commit()

    return result