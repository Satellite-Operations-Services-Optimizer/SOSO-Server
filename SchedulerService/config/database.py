from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.automap import automap_base
import os


db_engine = None
db_session = None
Base = None

Satellite = None
GroundStation = None
ImageOrder = None
Schedule = None
MaintenanceOrder = None
OutageOrder = None

load_dotenv()
def setup_database():
    global db_engine, db_session, Base

    driver = os.environ['DB_DRIVER']
    user = os.environ['DB_USER']
    password = os.environ['DB_PASS']
    host = 'localhost' #This is not inside a docker container, so it connects locally
    db_name = os.environ['DB_NAME']
    schema = os.environ['DB_SCHEMA']
    schema = schema if len(schema) > 0 else None

    # Create database endine
    db_url = f"{driver}://{user}:{password}@{host}/{db_name}"
    db_engine = create_engine(db_url)

    # Automap to reflect all tables in database
    metadata = MetaData(schema=schema)
    Base = automap_base(metadata=metadata)
    Base.prepare(autoload_with=db_engine)

    # Create database session (scoped_session is used just to make sure the connection is thread safe)
    DatabaseSession = scoped_session(sessionmaker(bind=db_engine))
    db_session = DatabaseSession()


def setup_database_tables():
    global Base
    global Satellite, GroundStation, ImageOrder, Schedule, MaintenanceOrder, OutageOrder

    Satellite = Base.classes.satellite
    GroundStation = Base.classes.ground_station
    ImageOrder = Base.classes.image_order
    Schedule = Base.classes.schedule
    MaintenanceOrder = Base.classes.maintenance_order
    OutageOrder = Base.classes.outage_order
    ScheduleEvent = Base.classes.schedule_event


setup_database()
setup_database_tables()
