from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import os

engine = None
Base = None

load_dotenv()
def setup_database(use_localhost=False):
    global engine, Base, _db_url

    session = get_session()
    if session is not None:
        session.close()

    driver = os.environ['DB_DRIVER']
    user = os.environ['DB_USER']
    password = os.environ['DB_PASS']
    host = os.environ['DB_HOST'] if use_localhost is False else 'localhost'
    db_name = os.environ['DB_NAME']
    schema = os.environ['DB_SCHEMA']
    schema = schema if len(schema) > 0 else None

    # Create database endine
    # We need to specify search path because sqlalchemy_utils.register_composites cannot see the schema we are using
    # https://stackoverflow.com/questions/59298580/how-to-specify-schema-in-psycopg2-connection-method
    _db_url = f"{driver}://{user}:{password}@{host}/{db_name}?options=-csearch_path%3D{schema},public"
    engine = create_engine(_db_url)

_global_session = None
def get_session():
    """
    Getter method for managing a single database session throughout lifetime of application (to avoid memory leaks)
    """
    global _global_session
    if _global_session is None or _global_session.is_active is False:
        if engine is None:
            return None
        # Create database session (scoped_session is used just to make sure the connection is thread safe)
        DatabaseSession = scoped_session(sessionmaker(bind=engine))
        _global_session = DatabaseSession()
    return _global_session

setup_database()