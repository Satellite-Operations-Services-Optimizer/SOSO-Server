from datetime import datetime, timedelta
from app_config import get_db_session
from app_config import logging
from .populate_orders import populate_sample_image_orders
from .populate_satellites import populate_sample_satellites
from .populate_groundstations import populate_sample_groundstations
from .populate_scheduled_events import populate_scheduled_events
from app_config.db_classes import GroundStation, ImageOrder, Schedule, MaintenanceOrder, OutageOrder, Satellite

logger = logging.getLogger(__name__)


def populate_database():
    populate_sample_satellites()
    populate_sample_groundstations()
    populate_sample_image_orders()
    populate_scheduled_events()

    logger.info("Populating `ground_station` table with random data...")
    populate_random_ground_stations()
    logger.info("Populating `image_orders` table with random data...")
    populate_random_image_orders()
    logger.info("Populating `schedule` table with random data...")
    populate_random_schedule()
    logger.info("Populating `maintenance_order` table with random data...")
    populate_random_maintenance_orders()
    logger.info("Populating `outage_order` table with random data...")
    populate_random_outage_orders()


import random
import pytz
import uuid
from app_config.database import *
# Ground Stations
def generate_random_ground_station():

    name = f"GroundStation_{uuid.uuid4()}"

    return {
        "name": name,
        "latitude": random.uniform(-90, 90),
        "longitude": random.uniform(-180, 180),
        "elevation": random.randint(0, 5000),
        "station_mask": random.randint(100,1000),
        "uplink_rate": random.randint(100, 10000),
        "downlink_rate": random.randint(100, 10000),
        "under_outage": random.choice([True, False]),
    }

def populate_random_ground_stations(num_ground_stations=10):
    ground_stations_data = [generate_random_ground_station() for _ in range(num_ground_stations)]

    ground_stations = []
    for data in ground_stations_data:
        ground_stations.append(
            GroundStation(
                name=data["name"],
                latitude=data["latitude"],
                longitude=data["longitude"],
                elevation=data["elevation"],
                station_mask=data["station_mask"],
                uplink_rate=data["uplink_rate"],
                downlink_rate=data["downlink_rate"],
                under_outage=data["under_outage"],
            )
        )

    db_session = get_db_session()
    db_session.add_all(ground_stations)
    db_session.commit()

# Image Orders
def generate_random_image_order():
    return {
        "latitude": random.uniform(-90, 90),
        "longitude": random.uniform(-180, 180),
        "priority": random.randint(1, 5),
        "image_type": random.choice(["High", "Medium", "Low"]),
        "image_height": random.randint(100, 1000),
        "image_width": random.randint(100, 1000),
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M:%S"),
        "delivery_deadline": (datetime.now() + timedelta(days=random.randint(30, 60))).strftime("%Y-%m-%d %H:%M:%S"),
        "num_of_revisits": random.randint(0, 5),
        "revisit_frequency": random.randint(1, 10),
        "revisit_frequency_units": random.choice(["Days","Hours","Minutes","Month"]),
    }

def populate_random_image_orders(num_orders=10):
    image_orders_data = [generate_random_image_order() for _ in range(num_orders)]

    image_orders = []
    for data in image_orders_data:
        image_orders.append(
            ImageOrder(
                latitude=data["latitude"],
                longitude=data["longitude"],
                priority=data["priority"],
                image_type=data["image_type"],
                image_height=data["image_height"],
                image_width=data["image_width"],
                start_time=data["start_time"],
                end_time=data["end_time"],
                delivery_deadline=data["delivery_deadline"],
                num_of_revisits=data["num_of_revisits"],
                revisit_frequency=data["revisit_frequency"],
                revisit_frequency_units=data["revisit_frequency_units"],
            )
        )

    db_session = get_db_session()
    db_session.add_all(image_orders)
    db_session.commit()

# Schedules
def generate_random_schedule():

    start_time = datetime.now() + timedelta(days=random.randint(1, 30))
    duration = timedelta(hours=random.randint(1, 6))
    end_time = start_time + duration

    return {
        "asset_type": random.randint(1,10),
        "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": random.choice(["Active", "Inactive"])
    }

def populate_random_schedule(num_schedules=10):
    db_session = get_db_session()

    schedules_data = [generate_random_schedule() for _ in range(num_schedules)]
    satellite_ids = [satellite.id for satellite in db_session.query(Satellite).all()]
    ground_station_ids = [station.id for station in db_session.query(GroundStation).all()]   

    schedules = []
    for data in schedules_data:
        satellite_id = random.choice(satellite_ids) if satellite_ids else None
        ground_station_id = random.choice(ground_station_ids) if ground_station_ids else None
        schedules.append(
            Schedule(
                satellite_id = satellite_id,
                ground_station_id = ground_station_id,
                asset_type=data["asset_type"],
                start_time=data["start_time"],
                end_time=data["end_time"],
                status=data["status"]
            )
        )

    db_session = get_db_session()
    db_session.add_all(schedules)
    db_session.commit()

# Maintenance Orders
def generate_random_maintenance_order():
    
    asset_names = ["Satellite1", "Satellite2", "Satellite3","Satellite4","Satellite5"]
    start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    end_time_str = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M:%S")
    
    # Convert string to datetime objects
    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")

    # Calculate duration as timedelta  
    # string in the "HH:MM:SS" format without days
    duration_timedelta = end_time - start_time
    hours, remainder = divmod(duration_timedelta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    duration_time_format = "{:02}:{:02}:{:02}".format(hours, minutes, seconds)

    return {
        "asset_name": random.choice(asset_names),
        "start_time": start_time,
        "end_time": end_time,
        "duration": duration_time_format,
        "repetition": random.randint(1,5),
        "frequency_max": random.randint(1, 10),
        "frequency_min": random.randint(1, 5),
        "operations_flag": random.choice([True, False]),
        "description": f"Random maintenance for {random.choice(asset_names)}"
    }

def populate_random_maintenance_orders(num_orders=10):
    maintenance_orders_data = [generate_random_maintenance_order() for _ in range(num_orders)]

    maintenance_orders = []
    for data in maintenance_orders_data:
        maintenance_orders.append(
            MaintenanceOrder(
                asset_name=data["asset_name"],
                start_time=data["start_time"],
                end_time=data["end_time"],
                duration=data["duration"],
                repetition=data["repetition"],
                frequency_max=data["frequency_max"],
                frequency_min=data["frequency_min"],
                operations_flag=data["operations_flag"],
                description=data["description"]
            )
        )

    db_session = get_db_session()
    db_session.add_all(maintenance_orders)
    db_session.commit()

# Outage Orders
def generate_random_outage_order():
    
    asset_names = ["Satellite1", "Satellite2", "Satellite3", "Satellite4","Satellite5"]
    start_time = datetime.now() + timedelta(days=random.randint(1, 30))
    outage_duration = timedelta(hours=random.randint(1, 6))
    end_time = start_time + outage_duration

    return {
        "asset_name": random.choice(asset_names),
        "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S")
    }

def populate_random_outage_orders(num_orders=10):
    outage_orders_data = [generate_random_outage_order() for _ in range(num_orders)]

    outage_orders = []
    for data in outage_orders_data:
        outage_orders.append(
            OutageOrder(
                asset_name=data["asset_name"],
                start_time=data["start_time"],
                end_time=data["end_time"]
            )
        )

    db_session = get_db_session()
    db_session.add_all(outage_orders)
    db_session.commit()




def format_datetime_with_timezone(dt, timezone):
    tz = pytz.timezone(timezone)
    formatted_dt = dt.astimezone(tz)
    return f"{formatted_dt.strftime('%Y-%m-%d %H:%M:%S')} {formatted_dt.strftime('%Z')}"

def format_timedelta(timedelta_obj):
    hours, remainder = divmod(timedelta_obj.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}"


if __name__ == '__main__':
    populate_database()