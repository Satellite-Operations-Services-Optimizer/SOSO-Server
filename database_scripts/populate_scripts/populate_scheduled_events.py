from app_config import get_db_session, logging
from app_config.database.mapping import Satellite, GroundStation, Schedule, ScheduledContact, ScheduledImaging, ScheduledMaintenance, ScheduleRequest, ImageOrder
from datetime import datetime, timedelta
from math import ceil

logger = logging.getLogger(__name__)

def populate_scheduled_events():
    logger.info("Populating various schedules...")
    create_single_sat_single_gs_valid_schedule(datetime.now())

def create_single_sat_single_gs_valid_schedule(start_time: datetime):
    session = get_db_session()
    schedule_name = "test_single_sat_single_gs_valid_schedule"
    schedule = Schedule(name=schedule_name)
    session.add(schedule)

    sat_1 = session.query(Satellite).first()
    gs_1 = session.query(GroundStation).first()
    logger.info(f"Populating schedule '{schedule_name}' with scheduled image orders using satellite '{sat_1.name}' and groundstation '{gs_1.name}'...")


    if not sat_1:
        raise Exception("No satellites in database. Need at least one satellite to create a schedule.")
    elif not gs_1:
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
        revisit_frequency=timedelta(days=1)
    )
    session.add(image_order)
    session.commit() # populate default fields for image_order
    schedule_image_order(image_order, schedule, sat_1, gs_1)


def schedule_image_order(order: ImageOrder, schedule: Schedule, satellite: Satellite, groundstation: GroundStation):
    requests = []

    session = get_db_session()
    # create repeated requests
    for visit_count in range(order.visit_count):
        window_start = order.start_time
        window_end = order.end_time
        requests.append(
            ScheduleRequest(
                schedule_id=order.schedule_id,
                order_id=order.id,
                order_type=order.order_type,
                window_start=window_start,
                window_end=window_end,
                duration=order.duration,
                uplink_size=order.uplink_size,
                downlink_size=order.downlink_size,
                delivery_deadline=window_end+timedelta(days=1), # it must be delivered max one day after the image's window end
                priority=order.priority
            )
        )
        order.visit_count -= 1
        order.start_time += order.revisit_frequency
        order.end_time += order.revisit_frequency
        session.commit()
    
    session.add_all(requests)
    session.commit()


    contact_duration = timedelta(minutes=10)
    first_contact = ScheduledContact(
        schedule_id=schedule.id,
        asset_id=satellite.id,
        groundstation_id=groundstation.id,
        start_time=requests[0].window_start - contact_duration,
        duration=timedelta(minutes=20)
    )
    session.add(first_contact)
    session.commit()

    # partition requests into three separate arrays, evenly based on index
    num_of_partitions = 3
    previous_contact = first_contact
    while len(requests)>0:

        scheduled_imaging_partition = []
        for _ in range(ceil(len(requests)/num_of_partitions)):
            try:
                request = requests.pop(0)
            except IndexError:
                continue
            if not request:
                break

            event_start_time = (request.window_end - request.duration)
            uplink_contact = previous_contact
            scheduled_imaging_partition.append(
                ScheduledImaging(
                    schedule_id=request.schedule_id,
                    request_id=request.id,
                    asset_id=satellite.id,
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
        downlink_contact = ScheduledContact(
            schedule_id=schedule.id,
            asset_id=satellite.id,
            groundstation_id=groundstation.id,
            start_time=scheduled_imaging_partition[-1].window_end,
            duration=timedelta(minutes=20)
        )
        session.add(downlink_contact)
        session.commit()
        for scheduled_imaging in scheduled_imaging_partition:
            scheduled_imaging.downlink_contact_id = downlink_contact.id
        session.add_all(scheduled_imaging_partition)
        session.commit()

        previous_contact = downlink_contact
    
    session.commit()