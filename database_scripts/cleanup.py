from pathlib import Path
from sqlalchemy import text
from sqlalchemy.orm import close_all_sessions
from app_config import db_engine, get_db_session
from app_config import logging
from app_config.database.setup import setup_database
from importlib import reload
import argparse
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

def drop_database_schema():
    logger.info("Deleting database...")

    close_all_sessions()
    session = get_db_session()
    # Terminate all connections to the database (prevents any blocking due to active connections or locks)
    session.execute(text(f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = current_database()
        AND pid <> pg_backend_pid();
    """))
    schema = os.getenv("DB_SCHEMA")
    session.execute(text(f'DROP SCHEMA IF EXISTS {schema} CASCADE;'))
    session.execute(text(f'CREATE SCHEMA {schema}'))

    session.commit()
    setup_database()


def rebuild_database_schema():
    logger.info("Rebuilding database...")
    sql_path = Path(__file__).with_name("soso.sql")
    with db_engine.connect() as conn:
        p = Path(sql_path)
        with p.open('r') as file:
            sql_text = file.read()
            conn.execute(text(sql_text))
            conn.commit()
    
    # remap the table names
    import app_config.database.mapping
    reload(app_config.database.mapping)

def populate_database(reference_time: Optional[datetime] = None):
    logger.info("Populating database...")
    from database_scripts.populate import populate_database
    populate_database(reference_time)

def set_reference_time(reference_time: Optional[datetime] = None):
    from database_scripts.populate import set_reference_time
    set_reference_time(reference_time)

    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--drop", action='store_true', default=False, help="Drop database, as well as all tables and data")
    parser.add_argument("-s", "--schema", action='store_true', default=False, help="Drop and rebuild database schema, without populating it")
    parser.add_argument("-p", "--populate", action='store_true', default=False, help="Rebuild and populate database")
    parser.add_argument("-t", "--reference-time", nargs='?', default=None, required=False, type=datetime.fromisoformat, help="Set the reference time of the schedule into which the order items will be populated into")

    args = parser.parse_args()


    if args.populate or (not args.schema and not args.drop): # default when no args set
        drop_database_schema()
        rebuild_database_schema()
        if args.reference_time:
            set_reference_time(args.reference_time)
        populate_database()
    elif args.schema:
        print("Rebuilding schema...")
        drop_database_schema()
        rebuild_database_schema()
        if args.reference_time:
            set_reference_time(args.reference_time)
    elif args.drop:
        drop_database_schema()
