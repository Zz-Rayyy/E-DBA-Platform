import os

SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL', 'mysql+pymysql://root@127.0.0.1:3306/E-DBA'
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
