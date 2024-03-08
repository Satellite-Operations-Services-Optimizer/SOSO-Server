from scheduler_service.event_processing.capture_opportunities import ensure_capture_opportunities_populated
from datetime import datetime, timedelta
from app_config import get_db_session
from app_config.database.mapping import Satellite, CaptureOpportunity, CaptureProcessingBlock, ImageOrder, Schedule, ScheduleRequest
from typing import Optional
import time


def test_accurate_capture_opportunity_population(test_satellite: Satellite, image_order: ImageOrder, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
    # start_time = datetime(2024, 2, 14, 2, 20, 45, 772453) + timedelta(hours=5.3)
    start_time = image_order.start_time
    end_time = image_order.delivery_deadline

    start = time.perf_counter()
    ensure_capture_opportunities_populated(start_time, end_time)
    finish = time.perf_counter()
    print(f'Finished in {round(finish-start, 2)} second(s)')
    return

    session = get_db_session()
    capture_opportunities_within_time_range = session.query(CaptureOpportunity.utc_time_range).filter(
        CaptureOpportunity.asset_id == test_satellite.id,
        CaptureOpportunity.image_type == image_order.image_type,
        CaptureOpportunity.latitude == image_order.latitude,
        CaptureOpportunity.longitude == image_order.longitude,
        CaptureOpportunity.utc_time_range.op('&&')(func.tsrange(start_time, end_time))
    ).order_by(SatelliteEclipse.start_time).all()

    expected_opportunities = deque([opportunity_db_row[0] for opportunity_db_row in capture_opportunities_within_time_range])
    current_opportunity = expected_opportunities.popleft() if expected_opportunitieis else None
    previous_opportunity_end = None
    for satellite_state in SatelliteStateGenerator(test_satellite).track(start_time, end_time):
        move_to_next_opportunity = satellite_state.time > current_opportunity.upper.replace(tzinfo=timezone.utc) if current_opportunity else False
        if move_to_next_opportunity:
            previous_opportunity_end = current_opportunity.upper.replace(tzinfo=timezone.utc) if current_opportunity else None
            current_opportunity = expected_opportunities.popleft() if expected_opportunities else None

        
        if current_opportunity is None:
            capture_opportunity_expected = False
        else:
            expected_opportunity_start = current_opportunity.lower.replace(tzinfo=timezone.utc)
            expected_opportunity_end = current_opportunity.upper.replace(tzinfo=timezone.utc)
            capture_opportunity_expected = satellite_state.time >= expected_opportunity_start and satellite_state.time <= expected_opportunity_end
        

        if capture_opportunity_expected:
            assert not satellite_state.is_sunlit
        else:
            # Don't throw an error if it is an undersampling problem.
            # Sampling rate for eclipse in the SatelliteStateGenerator.eclipse_events() method which is used by
            # the ensure_eclipse_events_populated() method uses a sampling rate of 1 minute.
            sampling_rate = timedelta(minutes=1)
            if previous_eclipse_end:
                is_undersampling_problem = abs(satellite_state.time - previous_eclipse_end) < sampling_rate
            elif not current_eclipse:
                # TODO verify logic
                is_undersampling_problem = current_eclipse and abs(satellite_state.time - current_eclipse.lower.replace(tzinfo=timezone.utc)) < sampling_rate
            else:
                is_undersampling_problem = False
            assert satellite_state.is_sunlit or is_undersampling_problem


def test():
    session = get_db_session()

    satellite = session.query(Satellite).filter_by(id=1).one()
    test_schedule_name = "test capture opportunity population schedule"

    test_schedule = session.query(Schedule).filter_by(name=test_schedule_name).first()
    if test_schedule:
        image_order = session.query(ImageOrder).filter_by(schedule_id=test_schedule.id).first()
        if image_order:
            test_accurate_capture_opportunity_population(satellite, image_order)
            return

    session.query(ImageOrder)
    test_schedule = Schedule(name=test_schedule_name)
    session.add(test_schedule)
    session.flush()


    lat = 48.043
    long = -179.132
    lat = -82.609
    long = 114.816



    lat = -80.0244459881869 
    long = -81.07364979151080
    image_order = ImageOrder(
        schedule_id=test_schedule.id,
        latitude=lat,
        longitude=long,
        image_type="medium",
        start_time=datetime(2024, 2, 10, 0, 0),
        end_time=datetime(2024, 2, 17, 0, 0),
        delivery_deadline=datetime(2024, 2, 17, 0, 0),
    )
    session.add(image_order)
    session.flush()
    image_order = session.query(ImageOrder).filter_by(id=image_order.id).one() # refresh to get trigger-populated field values

    request = ScheduleRequest(
        schedule_id=test_schedule.id,
        order_type="imaging",
        order_id=image_order.id,
        window_start=image_order.start_time,
        window_end=image_order.end_time,
        duration=image_order.duration,
        delivery_deadline=image_order.delivery_deadline,
        uplink_size=image_order.uplink_size,
        downlink_size=image_order.downlink_size,
        status="processing"
    )
    session.add(request)
    session.commit()

    test_accurate_capture_opportunity_population(satellite, image_order)

test()
