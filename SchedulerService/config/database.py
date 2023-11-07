from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import os

driver = os.getenv('DB_DRIVER')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASS')
host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')

db_url = f"{driver}://{user}:{password}@{host}/{db_name}"
engine = create_engine(db_url)

# scoped_session is used just to make sure the connection is thread safe
DatabaseSession = scoped_session(sessionmaker(bind=engine))
db_session = DatabaseSession()