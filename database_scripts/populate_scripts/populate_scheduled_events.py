from app_config import get_db_session
from app_config.database.mapping import Satellite, GroundStation, Schedule, ScheduledContact, ScheduledImaging, ScheduledMaintenance, ScheduleRequest, ImageOrder
from datetime import datetime, timedelta


def populate_scheduled_events():
    pass

def create_single_satellite_valid_schedule(start_time: datetime):
    session = get_db_session()
    schedule = Schedule(group_name="test_single_satellite_valid_schedule")
    session.add(schedule)

    sat_1 = session.query(Satellite).first()
    gs_1 = session.query(GroundStation).first()

    if not sat_1:
        raise Exception("No satellites in database. Need at least one satellite to create a schedule.")
    elif not gs_1:
        raise Exception("No ground stations in database. Need at least one ground station to create a schedule.")


    event_duration = timedelta(minutes=10)

    image_order_end_time = start_time + timedelta(hours=1) # take the photo anytime between start_time, and a day from start_time
    delivery_deadline = image_order_end_time + timedelta(days=1) # downlink the photo you took by this time
    image_order = ImageOrder(
        schedule_id=schedule.id,
        latitude=0.0,
        longitude=0.0,
        image_type='low_res',
        start_time=start_time,
        end_time=image_order_end_time,
        duration=event_duration,
        delivery_deadline=delivery_deadline,
        repeat_frequency=timedelta(days=1)
    )

    schedule_image_order(image_order, schedule, sat_1, gs_1)
    session.commit()


def schedule_image_order(order: ImageOrder, schedule: Schedule, satellite: Satellite, groundstation: GroundStation):
    requests = []

    # create repeated requests
    for revisit_count in range(order.number_of_revisits):
        window_start = order.start_time
        window_end = order.end_time
        requests.append(
            ScheduleRequest(
                schedule_id=order.schedule_id,
                order_id=order.id,
                order_type=order.order_type,
                window_start=window_start,
                window_end=window_end,
                duration=imaging_duration(order.image_type),
                delivery_deadline=window_end+timedelta(days=1), # it must be delivered max one day after the image's window end
                uplink_data_size=100.0,
                downlink_data_size=image_storage(order.image_type),
                priority=order.priority
            )
        )
        order.number_of_revisits -= 1
        order.start_time += order.revisit_frequency
        order.end_time += order.revisit_frequency
    
    session = get_db_session()
    session.add_all(requests)


    contact_duration = timedelta(minutes=10)
    first_contact = ScheduledContact(
        schedule_id=schedule.id,
        asset_id=satellite.id,
        groundstation_id=groundstation.id,
        start_time=requests[0].start_time - contact_duration,
        duration=timedelta(minutes=20)
    )
    session.add(first_contact)

    # partition requests into three separate arrays, evenly based on index
    num_of_partitions = 3
    previous_contact = first_contact
    while len(requests)>0:

        scheduled_imaging_partition = []
        for i in len(requests)/num_of_partitions:
            request = requests.pop(0, None)
            if not request:
                break

            event_start_time = (request.window_end - request.duration)
            uplink_contact = previous_contact
            scheduled_imaging_partition.append(
                ScheduledImaging(
                    schedule_id=request.schedule_id,
                    request_id=request.id,
                    start_time=event_start_time,
                    duration=request.duration,
                    window_start=request.window_start,
                    window_end=request.window_end,
                    uplink_contact_id=uplink_contact.id,
                    uplink_data_size=request.uplink_data_size,
                    downlink_contact_id=None, # we are soon going to create this
                    downlink_data_size=request.downlink_data_size,
                    priority=request.priority
                )
            )

        session.add_all(scheduled_imaging_partition)
        # create a downlink contact and add it as downlink_contact_id for every request in the partition
        downlink_contact = ScheduledContact(
            schedule_id=schedule.id,
            asset_id=satellite.id,
            groundstation_id=groundstation.id,
            start_time=scheduled_imaging_partition[-1].end_time,
            duration=timedelta(minutes=20)
        )
        session.add(downlink_contact)
        for scheduled_imaging in scheduled_imaging_partition:
            scheduled_imaging.downlink_contact_id = downlink_contact.id
        previous_contact = downlink_contact
        
def imaging_duration(image_type: str):
    if image_type=='low_res': return timedelta(minutes=1)
    elif image_type=='medium_res': return timedelta(minutes=3)
    elif image_type=='high_res': return timedelta(minutes=5)

def image_storage(image_type: str):
    if image_type=='low_res': return 5000.0
    elif image_type=='mid_res': return 10_000.0
    elif image_type=='high_res': return 20_000.0