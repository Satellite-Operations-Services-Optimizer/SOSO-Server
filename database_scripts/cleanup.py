from pathlib import Path
from sqlalchemy import text
from config.database import db_engine, Base
from config import logging
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


from populate.populate import *

# Populate Satellite table with satellite data
logger.info("Populating `satellite` table...")
populate_satellites_from_sample_tles()

# Populate Ground Station Table with ground station data
logger.info("Populating 'ground_station' table...")
populate_ground_stations()

# Populate Image Order Table with image order data
logger.info("Populating 'image_order' table...")
populate_image_orders()

# Populate Schedule from schedule date
logger.info("Populating 'schedule' table...")
populate_schedule()

# Populate Maintentance Orders from maintenance order data
logger.info("Populating 'maintenance_order' table...")
populate_maintenance_orders()

# Populate Outage Orders from outage order data
logger.info("Populating 'outage_order' table...")
populate_outage_orders()