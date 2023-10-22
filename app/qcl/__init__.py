import logging
import os
import sys

# setup logging
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - [%(module)s: %(funcName)s: %(lineno)d]: %(message)s"
)

stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(stream_handler)

# do rest of imports
from flask import Flask
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from qcl.config import Config

# create app and db
app = Flask(__name__)
app.secret_key = os.environ["FLASK_SESSION_KEY"]
app.config.from_object(Config)
db = SQLAlchemy(app)
cache = Cache(app)
cache.clear()

# set content security policy (CSP)
csp = {
    "default-src": "'self'",
    "script-src": [
        "'self'",
        "https://cdnjs.cloudflare.com",
        "https://cdn.datatables.net",
    ],
    "style-src": [
        "'self'",
        "https://cdnjs.cloudflare.com",
        "https://cdn.datatables.net",
    ],
    "img-src": ["'self'", "data:"],
}

# force HTTPS in production
https = os.environ["ENVIRONMENT"].lower() == "production"

# configure HTTP headers with talisman
talisman = Talisman(
    app,
    frame_options="DENY",
    content_security_policy=csp,
    content_security_policy_nonce_in=["script-src"],
    force_https=https,
    force_https_permanent=https,
    strict_transport_security=https,
    session_cookie_secure=https,
)

# load routes
import qcl.views.routes
