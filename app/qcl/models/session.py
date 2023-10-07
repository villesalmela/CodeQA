from qcl.utils import dbrunner, general, serialize
from flask import g
from qcl import app

SESSION_MAX_LIFETIME = 3600

class PSQLSession:

    @staticmethod
    def open(session_id) -> str:
        app.logger.debug("Opening existing session")
        g.psql_session_id = session_id
        query = "SELECT user_id, created, data FROM sessions WHERE session_id=:session_id"
        params = {"session_id": session_id}
        try:
            result = dbrunner.execute(query, params)
        except Exception as e:
            raise RuntimeError("Failed to read session") from e
        row = result.first()
        if row is None:
            raise ValueError("Session doesn't exist")
        created = row.created
        data = row.data
        user_id = row.user_id
        if created < general.get_current_time() - SESSION_MAX_LIFETIME:
            raise TimeoutError("Session expired")
        g.psql_session = serialize.decompress(data)
        g.psql_session_modified = False
        return user_id

    def __setitem__(self, key, value):
        g.psql_session[key] = value
        g.psql_session_modified = True

    def __getitem__(self, key):
        return g.psql_session[key]

    def __delitem__(self, key):
        del g.psql_session[key]
        g.psql_session_modified = True

    def __contains__(self, key):
        return key in g.psql_session

    @staticmethod
    def is_open() -> bool:
        return hasattr(g, "psql_session")
    
    @staticmethod
    def get(key):
        return g.psql_session.get(key)
    
    @staticmethod
    def new(user_id: str) -> str:
        data = {}
        app.logger.debug("Creating new session")
        query = "INSERT INTO sessions (user_id, data) VALUES (:user_id, :data) RETURNING session_id"
        data_bytes = serialize.compress(data)
        params = {"user_id": user_id, "data": data_bytes}
        try:
            result = dbrunner.execute(query, params)
        except Exception as e:
            raise RuntimeError("Failed to create session") from e
        row = result.first()
        session_id = row.session_id
        g.psql_session = data
        g.psql_session_id = session_id
        g.psql_session_modified = False
        return session_id

    @staticmethod
    def save() -> None:
        app.logger.debug("Saving session")
        if g.psql_session_modified:
            app.logger.debug("Session modified, writing to db")
            query = "UPDATE sessions SET data=:data WHERE session_id=:session_id"
            data = serialize.compress(g.psql_session)
            params = {"session_id": g.psql_session_id, "data": data}
            try:
                dbrunner.execute(query, params)
            except Exception as e:
                raise RuntimeError("Failed to write session") from e
        else:
            app.logger.debug("Session NOT modified, NOT writing to db")
            
    @staticmethod
    def delete() -> None:
        app.logger.debug("Deleting session")
        query = "DELETE FROM sessions WHERE session_id=:session_id"
        params = {"session_id": g.psql_session_id}
        try:
            dbrunner.execute(query, params)
        except Exception as e:
            raise RuntimeError("Failed to delete session") from e
        attrs = ["psql_session", "psql_session_id", "psql_session_modified"]
        for a in attrs:
            delattr(g, a)
        

server_session = PSQLSession()