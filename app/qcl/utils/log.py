from qcl.utils import dbrunner
from qcl import app

# create log entry for login event
def login(user_id: str, success: bool, remote_ip: str, reason: str=""):
    query = "INSERT INTO auth_events (user_id, event_type, success, remote_ip, reason) \
        VALUES (:user_id, 'login', :success, :remote_ip, :reason)"
    params = {"user_id": user_id, "success": success, "reason": reason, "remote_ip": remote_ip}
    try:
        dbrunner.execute(query, params)
    except Exception as e:
        raise RuntimeError("Failed to log login event") from e

# create log entry for account verification
def verification(user_id: str, success: bool, remote_ip: str):
    query = "INSERT INTO auth_events (user_id, event_type, success, remote_ip) \
        VALUES (:user_id, 'verification', :success, :remote_ip)"
    params = {"user_id": user_id, "success": success, "remote_ip": remote_ip}
    try:
        dbrunner.execute(query, params)
    except Exception as e:
        raise RuntimeError("Failed to log verification event") from e

# create log entry for account creation
def account_creation(user_id: str, success: bool, remote_ip: str, reason: str=""):
    query = "INSERT INTO account_events (user_id, event_type, success, remote_ip, reason) \
        VALUES (:user_id, 'create', :success, :remote_ip, :reason)"
    params = {"user_id": user_id, "success": success, "reason": reason, "remote_ip": remote_ip}
    try:
        dbrunner.execute(query, params)
    except Exception as e:
        raise RuntimeError("Failed to log account creation event") from e