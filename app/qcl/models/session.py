from qcl.utils import dbrunner, compress, general
from flask import redirect, url_for
import flask

SESSION_MAX_LIFETIME = 3600

class PSQLSession:

    def __init__(self, session_id) -> None:
        self.session_id = session_id
        query = "SELECT created, data FROM sessions WHERE session_id=:session_id"
        params = {"session_id": session_id}
        success, result = dbrunner.execute(query, params)
        if not success:
            raise RuntimeError("Failed to read session")
        row = result.first()
        created = row.created
        data = row.data
        if created > general.get_current_time + SESSION_MAX_LIFETIME:
            return redirect(url_for("session_expired"))
        flask.g.psql_session = compress.decompress(data)

    def save(self) -> None:
        query = "UPDATE sessions SET data=:data WHERE session_id=:session_id"
        data = compress.compress(flask.g.psql_session)
        params = {"session_id": self.session_id, "data": data}
        success, _ = dbrunner.execute(query, params)
        if not success:
            raise RuntimeError("Failed to write session")
