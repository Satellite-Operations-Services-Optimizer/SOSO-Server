from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.automap import automap_base
import os

load_dotenv()

driver = os.environ['DB_DRIVER']
user = os.environ['DB_USER']
password = os.environ['DB_PASS']
host = 'localhost' #This is not inside a docker container, so it connects locally
db_name = os.environ['DB_NAME']
schema = os.environ['DB_SCHEMA']
schema = schema if len(schema) > 0 else None

# Create database endine
db_url = f"{driver}://{user}:{password}@{host}/{db_name}"
db_engine = create_engine(db_url)

# Automap to reflect all tables in database
metadata = MetaData(schema=schema)
Base = automap_base(metadata=metadata)
Base.prepare(autoload_with=db_engine)

# Create database session (scoped_session is used just to make sure the connection is thread safe)
DatabaseSession = scoped_session(sessionmaker(bind=db_engine))
db_session = DatabaseSession()