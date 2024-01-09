from pathlib import Path
from sqlalchemy import text
from config.database import db_engine, get_session, Base
from config import logging
from config.database import setup_database, assign_database_tables
from populate_scripts.populate import populate_database
import os

logger = logging.getLogger(__name__)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def drop_database_schema():
    logger.info("Deleting database...")

    session = get_session()
    schema = os.getenv("DB_SCHEMA")
    session.execute(text(f'DROP SCHEMA IF EXISTS {schema} CASCADE;'))
    session.execute(text(f'CREATE SCHEMA {schema}'))

    session.commit()
    setup_database()


def rebuild_database(sql_path: str):
    logger.info("Rebuilding database...")
    with db_engine.connect() as conn:
        p = Path(sql_path)
        with p.open('r') as file:
            sql_text = file.read()
            conn.execute(text(sql_text))
            conn.commit()
    setup_database()
    assign_database_tables()
    print("hi")
    
if __name__ == "__main__":
    drop_database_schema()
    
    sql_path = Path(__file__).with_name("soso.sql")
    rebuild_database(sql_path)
    populate_database()