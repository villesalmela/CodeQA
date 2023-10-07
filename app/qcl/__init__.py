# setup logging
import logging
import sys
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(module)s: %(funcName)s: %(lineno)d]: %(message)s')

stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(stream_handler)

# do rest of imports
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from qcl.config import Config

# create app and db
app = Flask(__name__)
app.secret_key = os.environ["FLASK_SESSION_KEY"]
app.config.from_object(Config)
db = SQLAlchemy(app)

# load routes
import qcl.views.routes