from scheduler_service.event_processing.capture_opportunities import ensure_capture_opportunities_populated
from datetime import datetime, timedelta
from app_config import get_db_session
from app_config.database.mapping import Satellite, CaptureOpportunity, CaptureProcessingBlock, ImageOrder
from typing import Optional


def test_accurate_capture_opportunity_population(test_satellite: Satellite, image_order: ImageOrder, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None):
    # start_time = datetime(2024, 2, 14, 2, 20, 45, 772453) + timedelta(hours=5.3)
    start_time = datetime.utcnow() if start_time is None else start_time
    end_time = start_time + timedelta(days=1) if start_time is None or end_time is None else end_time
    ensure_capture_opportunities_populated(start_time, end_time)
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


session = get_db_session()
for satellite in session.query(Satellite).all():
    image_order = session.query(ImageOrder).first()
    test_accurate_capture_opportunity_population(satellite, image_order)
    exit()

print("done")