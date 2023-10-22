import os

db_password = os.environ["DB_PASSWORD"]
db_host = os.environ["DB_HOST"]
db_user = os.environ["DB_USER"]
db_name = os.environ["DB_NAME"]
db_port = os.environ["DB_PORT"]

CACHE_DIR = "/tmp/flask"
os.makedirs(CACHE_DIR, exist_ok=True)


class Config:
    SQLALCHEMY_DATABASE_URI = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"
    MAX_CONTENT_LENGTH = 1000000
    CACHE_DIR = CACHE_DIR
    CACHE_TYPE = "FileSystemCache"
    CACHE_IGNORE_ERRORS = True
