from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import os

load_dotenv()

driver = os.environ['DB_DRIVER']
user = os.environ['DB_USER']
password = os.environ['DB_PASS']
host = os.environ['DB_HOST']
db_name = os.environ['DB_NAME']

db_url = f"{driver}://{user}:{password}@{host}/{db_name}"
db_engine = create_engine(db_url)

# scoped_session is used just to make sure the connection is thread safe
DatabaseSession = scoped_session(sessionmaker(bind=db_engine))
db_session = DatabaseSession()