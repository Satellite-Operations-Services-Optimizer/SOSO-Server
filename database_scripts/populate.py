from datetime import datetime, timedelta
from app_config import logging
from app_config.database import get_session
from app_config.database.mapping import Schedule
from database_scripts.populate_scripts.populate_image_orders import populate_image_orders
from database_scripts.populate_scripts.populate_satellites import populate_satellites
from database_scripts.populate_scripts.populate_groundstations import populate_groundstations
from database_scripts.populate_scripts.populate_scheduled_events import populate_scheduled_events
from database_scripts.populate_scripts.populate_maintenance_orders import populate_maintenance_orders
from database_scripts.populate_scripts.populate_outage_orders import populate_outage_orders
import argparse
from pathlib import Path
import os
from datetime import datetime
from typing import Union
import sys

logger = logging.getLogger(__name__)

def set_reference_time(reference_time: Union[datetime, str]):
    session = get_session()
    if type(reference_time)==str:
        reference_time = datetime.fromisoformat(reference_time)
    print(f"Setting reference time to {reference_time}. schedule={os.getenv('DEFAULT_SCHEDULE_ID')}")
    session.query(Schedule).filter_by(id=os.getenv("DEFAULT_SCHEDULE_ID")).update(dict(
        reference_time=reference_time,
        time_offset=reference_time - datetime.now()
    ))
    session.commit()

samples_folder = Path(__file__).parent / 'sample_data'
def populate_database():
    populate_satellites(samples_folder / 'sample_satellites')
    populate_groundstations(samples_folder / 'sample_groundstations')
    populate_image_orders(samples_folder / 'sample_image_orders')
    populate_maintenance_orders(samples_folder / 'sample_maintenance_orders')
    populate_outage_orders(samples_folder / 'sample_outage_orders')
    # populate_scheduled_events()

    # populate_random_ground_stations()
    # populate_random_image_orders()
    # populate_random_maintenance_orders()
    # populate_random_outage_orders()
    # populate_random_schedule()


import random
import pytz
import uuid
from app_config.database.mapping import GroundStation, ImageOrder, Schedule, MaintenanceOrder, SatelliteOutageOrder, Satellite
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
    logger.info("Populating `ground_station` table with random data...")
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

    session = get_session()
    session.add_all(ground_stations)
    session.commit()

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
    logger.info("Populating `image_orders` table with random data...")
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

    session = get_session()
    session.add_all(image_orders)
    session.commit()

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
    logger.info("Populating `schedule` table with random data...")
    session = get_session()

    schedules_data = [generate_random_schedule() for _ in range(num_schedules)]
    satellite_ids = [satellite.id for satellite in session.query(Satellite).all()]
    ground_station_ids = [station.id for station in session.query(GroundStation).all()]   

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

    session = get_session()
    session.add_all(schedules)
    session.commit()

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
    logger.info("Populating `maintenance_order` table with random data...")
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

    session = get_session()
    session.add_all(maintenance_orders)
    session.commit()

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
    logger.info("Populating `outage_order` table with random data...")
    outage_orders_data = [generate_random_outage_order() for _ in range(num_orders)]

    outage_orders = []
    for data in outage_orders_data:
        outage_orders.append(
            SatelliteOutageOrder(
                asset_name=data["asset_name"],
                start_time=data["start_time"],
                end_time=data["end_time"]
            )
        )

    session = get_session()
    session.add_all(outage_orders)
    session.commit()




def format_datetime_with_timezone(dt, timezone):
    tz = pytz.timezone(timezone)
    formatted_dt = dt.astimezone(tz)
    return f"{formatted_dt.strftime('%Y-%m-%d %H:%M:%S')} {formatted_dt.strftime('%Z')}"

def format_timedelta(timedelta_obj):
    hours, remainder = divmod(timedelta_obj.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--satellites", nargs='?', default=None, required=False, help="Path to the file containing assets data")
    parser.add_argument("-g", "--groundstations", nargs='?', default=None, required=False, help="Path to the file containing assets data")
    parser.add_argument("-i", "--imaging", nargs='?', default=None, required=False, help="Path to the file containing imaging data")
    parser.add_argument("-m", "--maintenance", nargs='?', default=None, required=False, help="Path to the file containing maintenance data")
    parser.add_argument("-o", "--outages", nargs='?', default=None, required=False, help="Path to the file containing outage data")
    # parser.add_argument("-p", "--schedule",action='store_true', default=False, help="Path to the file containing schedule data")
    parser.add_argument("--emit",action='store_true', default=True, help="Boolean flag whether to emit events to rabbitmq")
    parser.add_argument("-t", "--reference_time", nargs='?', default=None, required=False, type=datetime.fromisoformat, help="Set the reference time of the schedule into which the order items will be populated into")

    args = parser.parse_args()

    if args.reference_time:
        set_reference_time(args.reference_time)

    satellites_flag = '--satellites' in sys.argv or '-s' in sys.argv
    groundstations_flag = '--groundstations' in sys.argv or '-g' in sys.argv
    imaging_flag = '--imaging' in sys.argv or '-i' in sys.argv
    maintenance_flag = '--maintenance' in sys.argv or '-m' in sys.argv
    outages_flag = '--outages' in sys.argv or '-o' in sys.argv

    if satellites_flag:
        if args.satellites:
            populate_satellites(args.satellites, emit=args.emit)
        else:
            populate_satellites(samples_folder / 'sample_satellites', emit=args.emit)

    if groundstations_flag:
        if args.groundstations:
            populate_groundstations(args.groundstations, emit=args.emit)
        else:
            populate_groundstations(samples_folder / 'sample_groundstations', emit=args.emit)

    if imaging_flag:
        if args.imaging:
            print("Populating image orders from", args.imaging)
            populate_image_orders(args.imaging, emit=args.emit)
        else:
            print("Populating image orders from", samples_folder / 'sample_image_orders')
            populate_image_orders(samples_folder / 'sample_image_orders', emit=args.emit)

    if maintenance_flag:
        if args.maintenance:
            populate_maintenance_orders(args.maintenance, emit=args.emit)
        else:
            populate_maintenance_orders(samples_folder / 'sample_maintenance_orders', emit=args.emit)

    if outages_flag:
        if args.outages:
            populate_outage_orders(args.outages, emit=args.emit)
        else:
            populate_outage_orders(samples_folder / 'sample_outage_orders', emit=args.emit)
    # if '--schedule' in sys.argv:
    #     # populate_sample_schedules()
    #     populate_scheduled_events()


    if not maintenance_flag and not groundstations_flag and not imaging_flag and not maintenance_flag and not outages_flag:
        populate_database()
    