from qcl import app, db
from sqlalchemy.sql import text
from sqlalchemy.engine import Result
import traceback
import time
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


def new_users_count_total() -> int:
    time_filter = int(time.time()) - (24 * 60 * 60)
    query = "SELECT COUNT(*) FROM account_events WHERE event_type='create' AND event_time > :time_filter"
    params = {"time_filter": time_filter}
    success, result = execute(query, params)
    if not success:
        raise RuntimeError(result)
    count = result.first()[0]
    assert isinstance(count, int)
    return count

def new_users_count_ip(remote_ip: str) -> int:
    time_filter = int(time.time()) - (24 * 60 * 60)
    query = "SELECT COUNT(*) FROM account_events WHERE event_type='create' AND remote_ip=:remote_ip AND event_time > :time_filter"
    params = {"time_filter": time_filter, "remote_ip": remote_ip}
    success, result = execute(query, params)
    if not success:
        raise RuntimeError(result)
    count = result.first()[0]
    assert isinstance(count, int)
    return count

def save_function(code: str, tests: str, keywords: str, usecase: str, name: str, uid: str) -> tuple[bool, str]:
    query = "INSERT INTO functions (code, tests, keywords, usecase, name, uid) \
        VALUES (:code, :tests, :keywords, :usecase, :name, :uid)"
    params = {"code": code, "tests": tests, "keywords": keywords, "usecase": usecase, "name": name, "uid": uid}
    success, _ = execute(query, params)
    if not success:
        return False, ""
    query = "SELECT function_id FROM functions WHERE name=:name"
    params = {"name": name}
    success, result = execute(query, params)
    if not success:
        return False, ""
    function_id = result.first()[0]
    return True, function_id
        

def get_function(function_id: int):
    query = "SELECT f.name as name, f.code as code, f.tests as tests, f.usecase as usecase, f.keywords as keywords, u.username as username \
        FROM functions AS f \
        JOIN users AS u ON f.uid = u.uid \
        WHERE f.function_id = :function_id;"
    params = {"function_id": function_id}
    success, result = execute(query, params)
    if not success:
        raise RuntimeError("Function fetch failed")
    row = result.first()
    if row is None:
        raise ValueError("Function not found")
    return {"name": row.name, "code": row.code, "tests": row.tests, "usecase": row.usecase, "keywords": row.keywords, "username": row.username}

def list_functions():
    query = "SELECT f.function_id, f.name as name, f.usecase as usecase, f.keywords as keywords, u.username as username \
        FROM functions AS f \
        JOIN users AS u ON f.uid = u.uid"
    success, result = execute(query)
    if not success:
        raise RuntimeError("Function fetch failed")
    return result.all()