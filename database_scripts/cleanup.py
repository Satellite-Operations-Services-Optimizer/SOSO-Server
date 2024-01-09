from pathlib import Path
from sqlalchemy import text
from config.database import db_engine, get_session
from config import logging
from config.database import assign_database_tables
from database_scripts.populate.populate import populate_database
import os

logger = logging.getLogger(__name__)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def drop_database_schema():
    logger.info("Deleting database...")
    session = get_session()
    session.execute(text(f'DROP SCHEMA IF EXISTS {os.getenv("DB_SCHEMA")} CASCADE;'))
    session.commit()


def rebuild_database(sql_path: str):
    logger.info("Rebuilding database...")
    with db_engine.connect() as conn:
        p = Path(sql_path)
        with p.open('r') as file:
            sql_text = file.read()
            conn.execute(text(sql_text))
            conn.commit()
    assign_database_tables()
    
if __name__ == "__main__":
    drop_database_schema()

    #prematurely exit script
    exit()

    sql_path = Path(__file__).with_name("soso.sql")
    rebuild_database(sql_path)
    populate_database()