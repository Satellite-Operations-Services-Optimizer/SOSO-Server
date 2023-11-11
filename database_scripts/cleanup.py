from pathlib import Path
from sqlalchemy import text
from config.database import db_engine, Base
from config import logging
from satellite.populate import populate_satellites_from_sample_tles

logger = logging.getLogger(__name__)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Delete all tables in database
logger.info("Deleting database tables...")
Base.metadata.drop_all(bind=db_engine)

# Rebuild database tables using `soso.sql`
logger.info("Rebuilding database...")
with db_engine.connect() as conn:
    p = Path(__file__).with_name("soso.sql")
    with p.open('r') as file:
        sql_text = file.read()
        conn.execute(text(sql_text))
        conn.commit()

# Populate Satellite table with satellite data
logger.info("Populating `satellite` table...")
populate_satellites_from_sample_tles()