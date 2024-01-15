from setup import engine
from sqlalchemy import Column, Integer
from sqlalchemy.ext.automap import automap_base
from app_config.utils import snake_to_camel_case
from sqlalchemy import MetaData
import os

schema = os.getenv('DB_SCHEMA', None)

metadata = MetaData(schema=schema)
Base = automap_base(metadata=metadata)

# ===== Map views/tables without primary keys
# we have to manually map views cuz automap doesn't do it. make sure to specify primary key fields for them to be able to be mapped.
# I haven't figured out how to properly map views yet, so this code doesn't work quite yet. I'll come back to it.
# class ScheduledImaging(Base):
#     __tablename__ = 'scheduled_imaging'
#     id = Column(Integer, primary_key=True)
#     autoload=True
#     autoload_with=engine

class SatelliteStateChange(Base):
    __tablename__ = 'satellite_state_change'
    id = Column(Integer, primary_key=True)
    autoload_with=engine


# ===== Perform auto-mapping
Base.prepare(autoload_with=engine, reflect=True)


# ===== export the tables to the global namespace, so we can import any table from the database from this file
# first delete the previously exported classes, in the case that this module is reloaded to remap database
if 'db_classes' not in globals():
    globals()['db_classes'] = []
for db_class_name in globals()['db_classes']:
    del globals()[db_class_name]

# expose the tables to the global namespace
for db_class in Base.classes:
    db_class.__name__ = snake_to_camel_case(db_class.__name__)
    globals()[db_class.__name__] = db_class