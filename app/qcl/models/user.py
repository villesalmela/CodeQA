from werkzeug.security import check_password_hash, generate_password_hash
from email_validator import validate_email
from qcl.utils import log, general, dbrunner, auth
from qcl.integrations import email
from qcl import app
from sqlalchemy.engine import Row
from qcl.models.session import SESSION_MAX_LIFETIME

USER_LOCKOUT_DURATION = 300


def new_users_count_total() -> int:
    "Return the number of new user accounts created within last 24 hours."

    time_filter = general.get_time_hours_ago(24)
    query = "SELECT COUNT(*) FROM account_events WHERE event_type='create' AND event_time > :time_filter"
    params = {"time_filter": time_filter}
    try:
        result = dbrunner.execute(query, params)
    except Exception as e:
        raise RuntimeError("Failed to retrieve amount of recently created users") from e
    count = result.first()[0]
    assert isinstance(count, int)
    return count

def new_users_count_ip(remote_ip: str) -> int:
    "Return the number of new user accounts created from this remote IP, within last 24 hours."

    time_filter = general.get_time_hours_ago(24)
    query = "SELECT COUNT(*) FROM account_events WHERE event_type='create' AND remote_ip=:remote_ip AND event_time > :time_filter"
    params = {"time_filter": time_filter, "remote_ip": remote_ip}
    try:
        result = dbrunner.execute(query, params)
    except Exception as e:
        raise RuntimeError("Failed to retrieve amount of recently created users, by remote ip") from e
    count = result.first()[0]
    assert isinstance(count, int)
    return count

def list_users() -> list[Row]:
    query = """
        SELECT u.user_id as user_id, u.username as username, u.admin as admin,
            u.verified as verified, u.disabled as disabled, u.created as created,
            u.locked as locked, s.sessions as sessions, f.functions as functions
        FROM users AS u
        LEFT JOIN (
            SELECT user_id, COUNT(*) as sessions FROM sessions
            WHERE created > :time_filter
            GROUP BY user_id
        ) AS s ON s.user_id = u.user_id
        LEFT JOIN (
            SELECT user_id, COUNT(*) as functions FROM functions GROUP BY user_id
        ) AS f ON f.user_id = u.user_id
        """
    time_filter = general.get_time_seconds_ago(SESSION_MAX_LIFETIME)
    params = {"time_filter": time_filter}
    result = dbrunner.execute(query, params)
    rows = result.all()
    return rows

class User:

    @staticmethod
    def new(username: str, password: str) -> None:
        
        username = validate_email(username, check_deliverability=False).normalized

        # Rate limiting, to prevent email spamming
        new_users_total = new_users_count_total()
        if new_users_total >= 5:
            raise PermissionError("Refused to create more than 5 users in a day")
        
        new_users_ip = new_users_count_ip(general.get_remote_ip())
        if new_users_ip >= 2:
            raise PermissionError("Refused to create more than 2 users in a day from single IP")

        verification_code = auth.get_verification_code()
        verification_code_hash = generate_password_hash(verification_code)
        try:
            email.send_verification_code(receiver=username, code=verification_code)
        except Exception as e:
            log.account_creation(user_id=None, success=False, remote_ip=general.get_remote_ip(), reason="Verification code sending failed")
            raise e
        
        query = "INSERT INTO users (username, password, verification_code) VALUES (:username, :password, :verification_code) RETURNING user_id"
        password_hash = generate_password_hash(password)
        params = {"username": username, "password": password_hash, "verification_code": verification_code_hash}
        try:
            result = dbrunner.execute(query, params)
        except Exception as e:
            log.account_creation(user_id=None, success=False, remote_ip=general.get_remote_ip(), reason="Insertion failed.")
            raise RuntimeError("User creation failed") from e
        
        row = result.first()
        user_id = row.user_id
        log.account_creation(user_id=user_id, success=True, remote_ip=general.get_remote_ip())


    def __init__(self, user_id=None, username=None) -> None:

        if user_id:    
            query = "SELECT user_id, username, password, verification_code, admin, verified, disabled, locked, created FROM users WHERE user_id=:user_id"
            params = {"user_id": user_id}
        elif username:
            query = "SELECT user_id, username, password, verification_code, admin, verified, disabled, locked, created FROM users WHERE username=:username"
            params = {"username": username}
        else:
            raise RuntimeError("Invalid parameters")
        try:
            result = dbrunner.execute(query, params)
        except Exception as e:
            raise RuntimeError("Failed to read user") from e
        row = result.first()
        if row is None:
            log.login(None, False, general.get_remote_ip(), "Used does not exist")
            app.logger.warning("User does not exist")
            raise ValueError("User does not exist")
        self.id = row.user_id
        self.name = row.username
        self.password_hash = row.password
        self.verification_code_hash = row.verification_code
        self.role = "admin" if row.admin else "user"
        self.disabled = row.disabled
        self.verified = row.verified
        self.created = row.created
        self.locked = True if row.locked and row.locked > general.get_time_seconds_ago(USER_LOCKOUT_DURATION) else False
    
    def check_verification_code(self, verification_code: str):
        remote_ip = general.get_remote_ip()
        verification_code = verification_code.replace(" ", "").replace("-", "")
        valid = check_password_hash(self.verification_code_hash, verification_code)
        if valid:
            app.logger.debug("correct verification code")
            log.verification(self.id, True, remote_ip)
            query = "UPDATE users SET verified=true WHERE user_id=:user_id"
            params = {"user_id": self.id}
            try:
                dbrunner.execute(query, params)
            except Exception as e:
                raise RuntimeError("Failed to update verification status") from e
            self.verified = True
            return True
        app.logger.debug("wrong verification code")
        log.verification(self.id, False, remote_ip)
        return False
    
    def check_status(self) -> str:
        """
        Returns either:
        - ok
        - unverified
        - rejected
        """
        if self.disabled or self.locked:
            return "rejected"
        elif not self.verified:
            return "unverified"
        else:
            return "ok"

    
    def login(self, password: str) -> str:
        """
        Returns either:
        - ok
        - invalid credentials
        - rejected
        """
        reason = self.check_status()
        if reason in ["ok", "unverified"]:
            # only check credentials if login is not rejected
            if check_password_hash(self.password_hash, password):
                app.logger.debug("correct password")
                reason = "ok"
            else:
                app.logger.debug("wrong password")
                reason = "invalid credentials"
            
        status = reason == "ok"
        remote_ip = general.get_remote_ip()
        log.login(self.id, status, remote_ip, reason)
        return reason
    
    def delete(self) -> None:
        app.logger.debug("Deleting user")
        query = "DELETE FROM users WHERE user_id=:user_id"
        params = {"user_id": self.id}
        try:
            dbrunner.execute(query, params)
        except Exception as e:
            raise RuntimeError("Failed to delete user") from e
        
    def disable(self) -> None:
        app.logger.debug("Disabling user")
        query = "UPDATE users SET disabled=TRUE WHERE user_id=:user_id"
        params = {"user_id": self.id}
        try:
            dbrunner.execute(query, params)
        except Exception as e:
            raise RuntimeError("Failed to disable user") from e
        
    def enable(self) -> None:
        app.logger.debug("Enabling user")
        query = "UPDATE users SET disabled=FALSE WHERE user_id=:user_id"
        params = {"user_id": self.id}
        try:
            dbrunner.execute(query, params)
        except Exception as e:
            raise RuntimeError("Failed to enable user") from e
        
    def lock(self) -> None:
        app.logger.debug("Locking user")
        query = "UPDATE users SET locked=EXTRACT(EPOCH FROM CURRENT_TIMESTAMP) WHERE user_id=:user_id"
        params = {"user_id": self.id}
        try:
            dbrunner.execute(query, params)
        except Exception as e:
            raise RuntimeError("Failed to lock user") from e
        
    def unlock(self) -> None:
        app.logger.debug("Unlocking user")
        query = "UPDATE users SET locked=NULL WHERE user_id=:user_id"
        params = {"user_id": self.id}
        try:
            dbrunner.execute(query, params)
        except Exception as e:
            raise RuntimeError("Failed to unlock user") from e
        
    def logout(self) -> None:
        app.logger.debug("Logging out user")
        query = "DELETE FROM sessions WHERE user_id=:user_id"
        params = {"user_id": self.id}
        try:
            dbrunner.execute(query, params)
        except Exception as e:
            raise RuntimeError("Failed to logout user") from e
        
    def promote(self) -> None:
        app.logger.debug("Promoting user to admin")
        query = "UPDATE users SET admin=TRUE WHERE user_id=:user_id"
        params = {"user_id": self.id}
        try:
            dbrunner.execute(query, params)
        except Exception as e:
            raise RuntimeError("Failed to promote user") from e
        
    def demote(self) -> None:
        app.logger.debug("Demoting admin to user")
        query = "UPDATE users SET admin=FALSE WHERE user_id=:user_id"
        params = {"user_id": self.id}
        try:
            dbrunner.execute(query, params)
        except Exception as e:
            raise RuntimeError("Failed to demote admin") from e
    