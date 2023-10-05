from qcl.utils import dbrunner, compress, general
from flask import redirect, url_for
import flask

SESSION_MAX_LIFETIME = 3600

class PSQLSession:

    @staticmethod
    def open(session_id) -> None:
        flask.g.psql_session_id = session_id
        query = "SELECT created, data FROM sessions WHERE session_id=:session_id"
        params = {"session_id": session_id}
        success, result = dbrunner.execute(query, params)
        if not success:
            raise RuntimeError("Failed to read session")
        row = result.first()
        if row is None:
            raise ValueError("Session doesn't exist")
        created = row.created
        data = row.data
        if created > general.get_current_time + SESSION_MAX_LIFETIME:
            return redirect(url_for("session_expired"))
        flask.g.psql_session = compress.decompress(data)
        flask.g.psql_session_modified = False

    def __setitem__(self, key, value):
        flask.g.psql_session[key] = value
        flask.g.psql_session_modified = True

    def __getitem__(self, key):
        return flask.g.psql_session[key]

    def __delitem__(self, key):
        del flask.g.psql_session[key]

    def __contains__(self, key):
        return key in flask.g.psql_session
    
    @staticmethod
    def new(user_id: str, data: dict) -> str:
        query = "INSERT INTO sessions (user_id, data) VALUES (:user_id, :data) RETURNING session_id"
        data_bytes = compress.compress(data)
        params = {"user_id": user_id, "data": data_bytes}
        success, result = dbrunner.execute(query, params)
        if not success:
            raise RuntimeError("Failed to create session")
        row = result.first()
        session_id = row.session_id
        flask.g.psql_session = data
        flask.g.psql_session_id = session_id
        flask.g.psql_session_modified = False
        return session_id

    @staticmethod
    def save() -> None:
        if flask.g.psql_session_modified:
            query = "UPDATE sessions SET data=:data WHERE session_id=:session_id"
            data = compress.compress(flask.g.psql_session)
            params = {"session_id": flask.g.psql_session_id, "data": data}
            success, _ = dbrunner.execute(query, params)
            if not success:
                raise RuntimeError("Failed to write session")

server_session = PSQLSession()