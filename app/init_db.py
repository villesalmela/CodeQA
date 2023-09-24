import os
import psycopg2
from pathlib import Path

# if not running in production, load env variables from file
if os.environ.get("ENVIRONMENT") == "production":
    pass
else:
    from dotenv import load_dotenv
    load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)


db_password = os.environ.get("DB_PASSWORD")
db_host = os.environ.get("DB_HOST")
db_user = os.environ.get("DB_USER")
db_name = os.environ.get("DB_NAME")
db_port = os.environ.get("DB_PORT")


def initialize_database():

    logging.info("Initializing database")
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
        sslmode="require"
    )

    cur = conn.cursor()

    # fetch the queries
    query = Path("schema.sql").read_text()
    
    # execute the queries
    cur.execute(query)

    # commit changes
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    initialize_database()
