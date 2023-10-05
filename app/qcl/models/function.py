from qcl.utils import dbrunner
from flask import session

def save_function(code: str, tests: str, keywords: str, usecase: str, name: str, user_id: str) -> tuple[bool, str]:
    query = "INSERT INTO functions (code, tests, keywords, usecase, name, user_id) \
        VALUES (:code, :tests, :keywords, :usecase, :name, :user_id)"
    params = {"code": code, "tests": tests, "keywords": keywords, "usecase": usecase, "name": name, "user_id": user_id}
    success, _ = dbrunner.execute(query, params)
    if not success:
        return False, ""
    query = "SELECT function_id FROM functions WHERE name=:name"
    params = {"name": name}
    success, result = dbrunner.execute(query, params)
    if not success:
        return False, ""
    function_id = result.first()[0]
    return True, function_id
        

def get_function(function_id: int):
    query = "SELECT f.user_id as user_id, f.name as name, f.code as code, f.tests as tests, f.usecase as usecase, f.keywords as keywords, u.username as username \
        FROM functions AS f \
        JOIN users AS u ON f.user_id = u.user_id \
        WHERE f.function_id = :function_id;"
    params = {"function_id": function_id}
    success, result = dbrunner.execute(query, params)
    if not success:
        raise RuntimeError("Function fetch failed")
    row = result.first()
    if row is None:
        raise ValueError("Function not found")
    return {"name": row.name, "code": row.code, "tests": row.tests, "usecase": row.usecase, "keywords": row.keywords, "username": row.username, "user_id": row.user_id}

def list_functions():
    query = "SELECT f.function_id, f.name as name, f.usecase as usecase, f.keywords as keywords, u.username as username \
        FROM functions AS f \
        JOIN users AS u ON f.user_id = u.user_id"
    success, result = dbrunner.execute(query)
    if not success:
        raise RuntimeError("Function fetch failed")
    return result.all()

def delete_function(function_id: int):
    query = "DELETE FROM functions WHERE function_id = :function_id;"
    params = {"function_id": function_id}
    success, _ = dbrunner.execute(query, params)
    return success
