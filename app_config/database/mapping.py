from setup import engine
from sqlalchemy import Column, Integer
from sqlalchemy.ext.automap import automap_base
from app_config.utils import snake_to_camel_case
from sqlalchemy import MetaData
import os

# metadata = MetaData(schema=schema)
# metadata.reflect(bind=engine, views=True)
# Base = automap_base(metadata=metadata)

schema = os.getenv('DB_SCHEMA', None)

metadata = MetaData(schema=schema)
Base = automap_base(metadata=metadata)

class ScheduledImaging(Base):
    __tablename__ = 'scheduled_imaging'
    id = Column(Integer, primary_key=True)
    autoload=True
    autoload_with=engine

class SatelliteStateChange(Base):
    __tablename__ = 'satellite_state_change'
    id = Column(Integer, primary_key=True)
    autoload_with=engine

# metadata.reflect(bind=engine, views=True)
Base.prepare(autoload_with=engine, reflect=True)
print("pause")

for db_class in Base.classes:
    db_class.__name__ = snake_to_camel_case(db_class.__name__)
    globals()[db_class.__name__] = db_class