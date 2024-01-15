from pathlib import Path
from sqlalchemy import text
from app_config import db_engine, get_db_session
from app_config import logging
from app_config.database.setup import setup_database
from importlib import reload
import os

logger = logging.getLogger(__name__)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def drop_database_schema():
    logger.info("Deleting database...")

    session = get_db_session()
    schema = os.getenv("DB_SCHEMA")
    session.execute(text(f'DROP SCHEMA IF EXISTS {schema} CASCADE;'))
    session.execute(text(f'CREATE SCHEMA {schema}'))

    session.commit()
    setup_database()


def rebuild_database_schema(sql_path: str):
    logger.info("Rebuilding database...")
    with db_engine.connect() as conn:
        p = Path(sql_path)
        with p.open('r') as file:
            sql_text = file.read()
            conn.execute(text(sql_text))
            conn.commit()
    
    # remap the table names
    import app_config.database.mapping
    reload(app_config.database.mapping)
    
    
if __name__ == "__main__":
    drop_database_schema()
    # exit() # uncomment this line to only drop the database, and not rebuild it
    
    sql_path = Path(__file__).with_name("soso.sql")
    rebuild_database_schema(sql_path)
    exit() # uncomment this line to only rebuild the database, and not populate it
    
    # we have to import it here, because the database tables might not be setup yet, and the populate scripts import the tables
    from populate_scripts.populate import populate_database
    populate_database()