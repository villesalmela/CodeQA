import os

db_password = os.environ.get("DB_PASSWORD")
db_host = os.environ.get("DB_HOST")
db_user = os.environ.get("DB_USER")
db_name = os.environ.get("DB_NAME")
db_port = os.environ.get("DB_PORT")

class Config:
    SQLALCHEMY_DATABASE_URI = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require'
    CODEMIRROR_LANGUAGES = ['python', 'yaml', 'htmlembedded']
    CODEMIRROR_THEME = 'material'
    WTF_CSRF_ENABLED = True