from qcl.utils import dbrunner, auth
from werkzeug.security import check_password_hash, generate_password_hash
import time
from flask import request
from qcl.utils import log
from email_validator import validate_email
from qcl.integrations import email
import logging
logging.basicConfig(level=logging.INFO)

MINUTES_15 = 60 * 15
def get_current_time() -> int:
    return int(time.time())

def get_remote_ip():
    if "X-Forwarded-For" in request.headers:
        return request.headers["X-Forwarded-For"]
    else:
        return request.remote_addr

class User:

    def __init__(self, username: str, password: str=None) -> None:
        
        username = validate_email(username, check_deliverability=False).normalized
        new_user = False

        if password: # new user

            new_users_total = dbrunner.new_users_count_total()
            if new_users_total >= 5:
                raise RuntimeError("Refused to create more than 5 users in a day")
            
            new_users_ip = dbrunner.new_users_count_ip(get_remote_ip())
            if new_users_ip >= 2:
                raise RuntimeError("Refused to create more than 2 users in a day from single IP")

            new_user = True
            password_hash = generate_password_hash(password)
            verification_code = auth.get_verification_code()
            logging.info(f"Verification_code: {verification_code}")
            verification_code_hash = generate_password_hash(verification_code)
            query = "INSERT INTO users (username, password, verification_code) VALUES (:username, :password, :verification_code)"
            params = {"username": username, "password": password_hash, "verification_code": verification_code_hash}
            success, _ = dbrunner.execute(query, params)
            if not success:
                log.account_creation(user_id=None, success=False, remote_ip=get_remote_ip(), reason="Insertion failed.")
                raise RuntimeError("User creation failed")
            send_success = email.send_verification_code(receiver=username, code=verification_code)
            if not send_success:
                log.account_creation(user_id=None, success=False, remote_ip=get_remote_ip(), reason="Verification code sending failed")
                raise RuntimeError("Verification code sending failed")
            # TODO: remove failed account from db
        query = "SELECT uid, password, verification_code, admin, verified, disabled, locked, created FROM users WHERE username=:username"
        params = {"username": username}
        success, result = dbrunner.execute(query, params)
        if not success:
            raise RuntimeError("Failed to read user")
        row = result.first()
        if row is None:
            log.login(None, False, get_remote_ip(), "Account does not exist")
            raise ValueError("User does not exist")
        self.id = row.uid

        if new_user:
            log.account_creation(user_id=self.id, success=True, remote_ip=get_remote_ip())

        self.name = username
        self.password_hash = row.password
        self.verification_code_hash = row.verification_code
        self.role = "admin" if row.admin else "user"
        self.disabled = row.disabled
        self.verified = row.verified
        self.created = row.created
        self.locked = True if row.locked and row.locked > get_current_time() - MINUTES_15 else False

    def check_password(self, password: str):
        return check_password_hash(self.password_hash, password)
    
    def check_verification_code(self, verification_code: str):
        remote_ip = get_remote_ip()
        verification_code = verification_code.replace(" ", "").replace("-", "")
        valid = check_password_hash(self.verification_code_hash, verification_code)
        if valid:
            log.verification(self.id, True, remote_ip)
            query = "UPDATE users SET verified=true WHERE uid=:user_id"
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
        remote_ip = get_remote_ip()
        
        log.login(self.id, log_status, remote_ip, reason)
        return status
    

