from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import os

# if not running in production, load env variables from file
if os.environ.get("ENVIRONMENT") == "production":
    pass
else:
    from dotenv import load_dotenv
    load_dotenv()

# config needs env variables
from qcl.config import Config

# create app and db
app = Flask(__name__)
app.secret_key = os.environ["FLASK_SESSION_KEY"]
app.config.from_object(Config)
db = SQLAlchemy(app)

# load routes
import qcl.views.routes