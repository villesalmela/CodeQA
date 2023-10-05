from qcl.utils import dbrunner, auth
from werkzeug.security import check_password_hash, generate_password_hash

from qcl.utils import log, general, dbrunner
from email_validator import validate_email
from qcl.integrations import email
import logging
logging.basicConfig(level=logging.INFO)


def new_users_count_total() -> int:
    "Return the number of new user accounts created within last 24 hours."

    time_filter = general.get_time_hours_ago(24)
    query = "SELECT COUNT(*) FROM account_events WHERE event_type='create' AND event_time > :time_filter"
    params = {"time_filter": time_filter}
    success, result = dbrunner.execute(query, params)
    if not success:
        raise RuntimeError(result)
    count = result.first()[0]
    assert isinstance(count, int)
    return count

def new_users_count_ip(remote_ip: str) -> int:
    "Return the number of new user accounts created from this remote IP, within last 24 hours."

    time_filter = general.get_time_hours_ago(24)
    query = "SELECT COUNT(*) FROM account_events WHERE event_type='create' AND remote_ip=:remote_ip AND event_time > :time_filter"
    params = {"time_filter": time_filter, "remote_ip": remote_ip}
    success, result = dbrunner.execute(query, params)
    if not success:
        raise RuntimeError(result)
    count = result.first()[0]
    assert isinstance(count, int)
    return count

class User:

    @staticmethod
    def new(username: str, password: str) -> str:
        
        username = validate_email(username, check_deliverability=False).normalized

        # Rate limiting, to prevent email spamming
        new_users_total = new_users_count_total()
        if new_users_total >= 5:
            raise RuntimeError("Refused to create more than 5 users in a day")
        
        new_users_ip = new_users_count_ip(general.get_remote_ip())
        if new_users_ip >= 2:
            raise RuntimeError("Refused to create more than 2 users in a day from single IP")

        password_hash = generate_password_hash(password)
        verification_code = auth.get_verification_code()
        verification_code_hash = generate_password_hash(verification_code)
        query = "INSERT INTO users (username, password, verification_code) VALUES (:username, :password, :verification_code) RETURNING user_id"
        params = {"username": username, "password": password_hash, "verification_code": verification_code_hash}
        success, result = dbrunner.execute(query, params)

        if not success:
            log.account_creation(user_id=None, success=False, remote_ip=general.get_remote_ip(), reason="Insertion failed.")
            raise RuntimeError("User creation failed")
        send_success = email.send_verification_code(receiver=username, code=verification_code)
        if not send_success:
            log.account_creation(user_id=None, success=False, remote_ip=general.get_remote_ip(), reason="Verification code sending failed")
            raise RuntimeError("Verification code sending failed")
            # TODO: remove failed account from db

        row = result.first()
        user_id = row.user_id
        log.account_creation(user_id=user_id, success=True, remote_ip=general.get_remote_ip())
        return user_id



    def __init__(self, username=None, password=None, user_id=None) -> None:
        need_credential_check = False
        need_session_check = False
        if username and password:
            query = "SELECT user_id, password, verification_code, admin, verified, disabled, locked, created FROM users WHERE username=:username"
            params = {"username": username}
            need_credential_check = True
        elif user_id:
            query = "SELECT user_id, password, verification_code, admin, verified, disabled, locked, created FROM users WHERE user_id=:user_id"
            params = {"user_id": user_id}
            need_session_check = True
        else:
            raise ValueError("Invalid parameters")
        success, result = dbrunner.execute(query, params)
        if not success:
            raise RuntimeError("Failed to read user")
        row = result.first()
        if row is None:
            log.login(None, False, general.get_remote_ip(), "Account does not exist")
            raise ValueError("User does not exist")
        self.id = row.user_id
        self.name = username
        self.password_hash = row.password
        self.verification_code_hash = row.verification_code
        self.role = "admin" if row.admin else "user"
        self.disabled = row.disabled
        self.verified = row.verified
        self.created = row.created
        self.locked = True if row.locked and row.locked > general.get_time_minutes_ago(15) else False

        if need_credential_check:
            credentials_valid = check_password_hash(self.password_hash, password)

        if need_session_check:
            
    
    def check_verification_code(self, verification_code: str):
        remote_ip = general.get_remote_ip()
        verification_code = verification_code.replace(" ", "").replace("-", "")
        valid = check_password_hash(self.verification_code_hash, verification_code)
        if valid:
            log.verification(self.id, True, remote_ip)
            query = "UPDATE users SET verified=true WHERE user_id=:user_id"
            params = {"user_id": self.id}
            success, _ = dbrunner.execute(query, params)
            if not success:
                raise RuntimeError("Failed to update verification status")
            self.verified = True
            return True
        log.verification(self.id, False, remote_ip)
        return False
    
    def login(self, password: str) -> bool|None:
        # return True if ok, False if rejected, None if missing verification
        password_valid = self.check_password(password)
    
        if password_valid and self.verified and not (self.disabled or self.locked):    
            status = True
            reason = ""
        elif password_valid and not (self.disabled or self.locked) and not self.verified:
            status = None
            reason = "Account not verified"
        else:
            status = False
            if self.disabled:
                reason = "Account disabled"
            elif self.locked:
                reason = "Account locked"
            else:
                reason = "Invalid credentials"
        
        log_status = status is True
        remote_ip = general.get_remote_ip()
        
        log.login(self.id, log_status, remote_ip, reason)
        return status
    

