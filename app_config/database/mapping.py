from app_config.database.setup import engine
from sqlalchemy import Column, Integer, DateTime, Float
from sqlalchemy.ext.automap import automap_base
from app_config.utils import snake_to_camel_case
from sqlalchemy import Table
from sqlalchemy import MetaData
from sqlalchemy_utils import CompositeType
from sqlalchemy_utils import register_composites
from psycopg2.extras import register_composite
import os

# references:
# automap view with no primary key, general code structure: https://stackoverflow.com/questions/48563367/sqlalchemy-automap-mssql-view-with-no-primary-key
# Table class arguments explained: https://pythonhosted.org/wechinelearn/_modules/sqlalchemy/sql/schema.html#:~:text=class%20Table(DialectKWArgs%2C%20SchemaItem%2C%20TableClause)
# example of declarative syntax for tables: https://stackoverflow.com/questions/4526498/sqlalchemy-declarative-syntax-with-autoload-reflection-in-pylons
# table config: https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/table_config.html
# reflect=True deprecated for sqlalchemy 2.0, use autoload_with=engine instead, otherwise it throws error: https://docs.sqlalchemy.org/en/20/changelog/migration_20.html#:~:text=%23%20use%20autoload_with%3Dengine


schema = os.getenv('DB_SCHEMA', None)
metadata = MetaData(schema=schema)
Base = automap_base(metadata=metadata)

# ============ Override/modify table definitions in orm =================
# NOTE: for views, as well as tables without a primary key field, we NEED to override definition and provide a primary key field, for it to be able to be automapped.
# but for tables with a primary key, overriding is optional, and you just have to specify the table name, and the fields you want to modify/add (e.g. look into relationship(), that is a situation where you may want to override a table definition, for easy joins on another related table)

# declarative syntax example in comments below: I could not get declarative syntax to work for tables without a primary key, so I used the Table syntax instead
# class ScheduledImaging(Base):
#     __tablename__ = 'scheduled_imaging'
#     id = Column(Integer, primary_key=True)
#     __table_args__ = {'autoload_with': engine, 'extend_existing': True}

# --- Define tables with Table syntax. This is the only way I could get it to automap for tables without a primary key

from sqlalchemy_utils import CompositeType
from sqlalchemy_utils.types.pg_composite import CompositeElement
from sqlalchemy.types import to_instance

# Fix for sqlalchemy_utils bug preventing querying with composite fields
# https://github.com/kvesteri/sqlalchemy-utils/issues/319#issuecomment-917180248
class _CompositeType(CompositeType):
    class comparator_factory(CompositeType.comparator_factory):
        def __getattr__(self, key):
            try:
                type_ = self.type.typemap[key]
            except KeyError:
                raise KeyError(
                    "Type '%s' doesn't have an attribute: '%s'" % (
                        object.__getattribute__(self, 'name'), key
                    )
                )

            element = CompositeElement(self.expr, key, type_)
            # Enable caching
            # https://docs.sqlalchemy.org/en/20/errors.html#error-cprf
            # https://docs.sqlalchemy.org/en/20/core/compiler.html#compilerext-caching
            # TODO: Warning is still showing up, so this doesn't work for some reason. fix later.
            element.inherit_cache = True 
            return element

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.typemap = dict((col.name, col.type) for col in self.columns)

AssetState = _CompositeType(
    'asset_state',
    [
        Column('storage', Float),
        Column('storage_util', Float),
        Column('throughput', Float)
    ]
)
# register_composite('asset_state', engine.connect().connection, globally=True)
# register_composites(engine.connect())

SatelliteStateChange = Table(
    'satellite_state_change', metadata,
    Column('schedule_id', Integer, primary_key=True),
    Column('asset_id', Integer, primary_key=True),
    Column('snapshot_time', DateTime(timezone=True), primary_key=True),
    Column('delta', AssetState),
    autoload_with=engine
)

GroundStationStateChange = Table(
    'ground_station_state_change', metadata,
    Column('schedule_id', Integer, primary_key=True),
    Column('asset_id', Integer, primary_key=True),
    Column('snapshot_time', DateTime(timezone=True), primary_key=True),
    Column('delta', AssetState),
    autoload_with=engine
)

StateCheckpoint = Table(
    'state_checkpoint', metadata,
    Column('state', AssetState),
    Column('delta_from_prev_chkpt', AssetState),
    Column('peak_delta_from_prev_chkpt', AssetState),
    autoload_with=engine
)
# ============ End of override/modify table definitions in orm =================


# ============ Automap the tables =================
Base.prepare(autoload_with=engine)
register_composites(engine.connect())
# ============ End of automap the tables =================


# ===== Export the tables to the global namespace, so we can import any table from the database from this file =====
# NOTE: this is not necessary, but it makes it easier to import tables from the database, and it makes the code more readable
# Example, we can import a table named 'scheduled_imaging' from the database like this:
# from app_config.database.mapping import ScheduledImaging


# first delete the previously exported classes, in the case that this module is reloaded to remap database
if 'db_classes' not in globals():
    globals()['db_classes'] = []
for db_class_name in globals()['db_classes']:
    del globals()[db_class_name]

# expose the tables to the global namespace
for db_class in Base.classes:
    db_class.__name__ = snake_to_camel_case(db_class.__name__)
    globals()[db_class.__name__] = db_class
    globals()['db_classes'].append(db_class.__name__)
# ===== End of export the tables to the global namespace =====
print("Database tables automapped and exported to global namespace")