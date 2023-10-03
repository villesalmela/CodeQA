#!/bin/sh

# Initialize the database
python init_db.py

# Start the Gunicorn server
exec gunicorn -c gunicorn_config.py qcl:app