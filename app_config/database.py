from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.automap import automap_base
import os


db_engine = None
Base = None

_db_url = None

load_dotenv()
def setup_database():
    global db_engine, Base, _db_url

    session = get_session()
    if session is not None:
        session.close()

    driver = os.environ['DB_DRIVER']
    user = os.environ['DB_USER']
    password = os.environ['DB_PASS']
    # host = 'localhost' #This is not inside a docker container, so it connects locally
    host = os.environ['DB_HOST']
    db_name = os.environ['DB_NAME']
    schema = os.environ['DB_SCHEMA']
    schema = schema if len(schema) > 0 else None

    # Create database endine
    _db_url = f"{driver}://{user}:{password}@{host}/{db_name}"
    db_engine = create_engine(_db_url)

    # Automap to reflect all tables in database
    metadata = MetaData(schema=schema)
    metadata.reflect(bind=db_engine, views=True)
    Base = automap_base(metadata=metadata)
    Base.prepare(autoload_with=db_engine)


_db_session = None
def get_session():
    """
    Getter method for managing a single database session throughout lifetime of application (to avoid memory leaks)
    """
    global _db_session
    if _db_session is None or _db_session.is_active is False:
        if db_engine is None:
            return None
        # Create database session (scoped_session is used just to make sure the connection is thread safe)
        DatabaseSession = scoped_session(sessionmaker(bind=db_engine))
        _db_session = DatabaseSession()
    return _db_session

setup_database()