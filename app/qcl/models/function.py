from qcl.utils import dbrunner
from typing import Any
from sqlalchemy.engine import Row

def save_function(code: str, tests: str, keywords: str, usecase: str, name: str, user_id: str) -> tuple[bool, str]:
    query = "INSERT INTO functions (code, tests, keywords, usecase, name, user_id) \
        VALUES (:code, :tests, :keywords, :usecase, :name, :user_id) RETURNING function_id"
    params = {"code": code, "tests": tests, "keywords": keywords, "usecase": usecase, "name": name, "user_id": user_id}
    try:
        result = dbrunner.execute(query, params)
    except Exception as e:
        raise RuntimeError("Failed to save function") from e
    function_id = result.first()[0]
    return function_id
        

def get_function(function_id: int) -> dict[str, Any]:
    query = "SELECT f.user_id as user_id, f.name as name, f.code as code, f.tests as tests, f.usecase as usecase, f.keywords as keywords, u.username as username \
        FROM functions AS f \
        JOIN users AS u ON f.user_id = u.user_id \
        WHERE f.function_id = :function_id;"
    params = {"function_id": function_id}
    try:
        result = dbrunner.execute(query, params)
    except Exception as e:
        raise RuntimeError("Failed to get function") from e
    row = result.first()
    if row is None:
        raise ValueError("Function not found")
    return row._asdict()

def list_functions() -> list[Row]:
    query = "SELECT f.function_id, f.name as name, f.usecase as usecase, f.keywords as keywords, u.username as username \
        FROM functions AS f \
        JOIN users AS u ON f.user_id = u.user_id"
    try:
        result = dbrunner.execute(query)
    except Exception as e:
        raise RuntimeError("Failed to list functions") from e
    return result.all()

def list_functions_by_user(user_id: str) -> list[Row]:
    query = "SELECT function_id, name, usecase, keywords FROM functions WHERE user_id=:user_id"
    params = {"user_id": user_id}
    try:
        result = dbrunner.execute(query, params)
    except Exception as e:
        raise RuntimeError("Failed to list functions") from e
    return result.all()

def delete_function(function_id: int) -> None:
    query = "DELETE FROM functions WHERE function_id = :function_id;"
    params = {"function_id": function_id}
    try:
        dbrunner.execute(query, params)
    except Exception as e:
        raise RuntimeError("Failed to deleted function") from e
