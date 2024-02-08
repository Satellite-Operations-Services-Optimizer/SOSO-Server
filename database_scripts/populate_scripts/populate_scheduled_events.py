from app_config import get_db_session, logging
from app_config.database.mapping import Satellite, GroundStation, Schedule, ContactOpportunity, ScheduledImaging, ScheduledMaintenance, ScheduleRequest, ImageOrder
from datetime import datetime, timedelta
from math import ceil
import random

logger = logging.getLogger(__name__)

def populate_scheduled_events():
    logger.info("Populating various schedules...")
    create_valid_image_order_schedule(datetime.now())

def create_valid_image_order_schedule(start_time: datetime):
    random.seed(123)
    session = get_db_session()
    schedule_name = "test_single_sat_single_gs_valid_schedule"
    schedule = Schedule(name=schedule_name, group_name="test_group")
    session.add(schedule)

    satellites = session.query(Satellite).limit(3).all()
    ground_stations = session.query(GroundStation).limit(2).all()
    logger.info(f"Populating schedule '{schedule_name}' with a scheduled image order using random satellites and groundstations...")


    if not len(satellites):
        raise Exception("No satellites in database. Need at least one satellite to create a schedule.")
    elif not len(ground_stations):
        raise Exception("No ground stations in database. Need at least one ground station to create a schedule.")


    image_order_end_time = start_time + timedelta(hours=1) # take the photo anytime between start_time, and a day from start_time
    delivery_deadline = image_order_end_time + timedelta(days=1) # downlink the photo you took by this time
    image_order = ImageOrder(
        schedule_id=schedule.id,
        latitude=0.0,
        longitude=0.0,
        image_type='medium_res',
        start_time=start_time,
        end_time=image_order_end_time,
        delivery_deadline=delivery_deadline,
        visits_remaining=15,
        revisit_frequency=timedelta(days=1)
    )
    session.add(image_order)
    session.commit() # populate default fields for image_order
    schedule_image_order(image_order, schedule, satellites, ground_stations)


def schedule_image_order(order: ImageOrder, schedule: Schedule, satellites: list[Satellite], ground_stations: list[GroundStation]):
    requests = []

    session = get_db_session()
    # create repeated requests
    for visit_count in range(order.visits_remaining):
        requests.append(
            ScheduleRequest(
                schedule_id=order.schedule_id,
                order_id=order.id,
                order_type=order.order_type,
                window_start=order.start_time,
                window_end=order.end_time,
                duration=order.duration,
                uplink_size=order.uplink_size,
                downlink_size=order.downlink_size,
                delivery_deadline=order.delivery_deadline,
                priority=order.priority
            )
        )
        order.visits_remaining -= 1
        order.start_time += order.revisit_frequency
        order.end_time += order.revisit_frequency
        order.delivery_deadline += order.revisit_frequency
        session.commit()
    
    session.add_all(requests)
    session.commit()


    contact_duration = timedelta(minutes=10)

    sat = random.choice(satellites)
    gs = random.choice(ground_stations)

    first_contact = ContactOpportunity(
        schedule_id=schedule.id,
        asset_id=sat.id,
        groundstation_id=gs.id,
        start_time=requests[0].window_start - contact_duration,
        duration=timedelta(minutes=20)
    )
    session.add(first_contact)
    session.commit()

    # partition requests into three separate arrays, evenly based on index
    num_of_partitions = 7
    uplink_contact = first_contact

    partition_count = 0
    while len(requests)>0:
        partition_count += 1

        scheduled_imaging_partition = []
        for count in range(ceil(len(requests)/num_of_partitions)):
            try:
                request = requests.pop(0)
            except IndexError:
                continue
            if not request:
                break

            event_start_time = (request.window_end - request.duration)
            scheduled_imaging_partition.append(
                ScheduledImaging(
                    schedule_id=request.schedule_id,
                    request_id=request.id,
                    asset_id=sat.id,
                    start_time=event_start_time,
                    duration=request.duration,
                    window_start=request.window_start,
                    window_end=request.window_end,
                    uplink_contact_id=uplink_contact.id,
                    uplink_size=request.uplink_size,
                    downlink_contact_id=None, # we are soon going to create this
                    downlink_size=request.downlink_size,
                    priority=request.priority
                )
            )

        # create a downlink contact and add it as downlink_contact_id for every request in the partition
        downlink_contact = ContactOpportunity(
            schedule_id=schedule.id,
            asset_id=sat.id,
            groundstation_id=gs.id,
            start_time=scheduled_imaging_partition[-1].window_end,
            duration=timedelta(minutes=20)
        )
        session.add(downlink_contact)

        new_sat = random.choice(satellites)
        new_gs = random.choice(ground_stations)

        if new_sat.id != sat.id or new_gs.id != gs.id:
            sat = new_sat
            gs = new_gs

            uplink_contact = ContactOpportunity(
                schedule_id=schedule.id,
                asset_id=sat.id,
                groundstation_id=gs.id,
                start_time=downlink_contact.start_time - contact_duration,
                duration=timedelta(minutes=20)
            )
            session.add(uplink_contact)
        else:
            uplink_contact = downlink_contact


        session.commit()
        for scheduled_imaging in scheduled_imaging_partition:
            scheduled_imaging.downlink_contact_id = downlink_contact.id
        session.add_all(scheduled_imaging_partition)
        session.commit()

        previous_contact = downlink_contact
    
    session.commit()