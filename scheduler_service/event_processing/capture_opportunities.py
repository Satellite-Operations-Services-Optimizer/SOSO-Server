from datetime import datetime
from scheduler_service.event_processing.utils import retrieve_and_lock_unprocessed_blocks_for_processing
from scheduler_service.satellite_state.state_generator import SatelliteStateGenerator
from app_config.database.mapping import Satellite, CaptureProcessingBlock, CaptureOpportunity, ScheduleRequest, ImageOrder
from app_config import get_db_session
from sqlalchemy import func, or_, distinct, exists, tuple_
from datetime import datetime, timedelta
import concurrent.futures
import loky

class SerializableCaptureProcessingBlock:
    def __init__(self, id: int, satellite_id: int, image_type: str, latitude: float, longitude: float, time_range):
        self.id = id
        self.satellite_id = satellite_id
        self.image_type = image_type
        self.latitude = latitude
        self.longitude = longitude
        self.time_range = time_range

class SerializableCaptureOpportunity:
    def __init__(self, asset_id: int, image_type: str, latitude: float, longitude: float, start_time: datetime, duration: timedelta):
        self.asset_id = asset_id
        self.image_type = image_type
        self.latitude = latitude
        self.longitude = longitude
        self.start_time = start_time
        self.duration = duration

def ensure_capture_opportunities_populated(start_time: datetime, end_time: datetime):
    session = get_db_session()

    start_time_no_tz = start_time.replace(tzinfo=None)
    end_time_no_tz = end_time.replace(tzinfo=None)
    exists_condition = exists().where(
        ScheduleRequest.schedule_id == ImageOrder.schedule_id,
        ScheduleRequest.order_id == ImageOrder.id,
        ScheduleRequest.order_type == ImageOrder.order_type,
        ScheduleRequest.utc_window_time_range.op('&&')(func.tsrange(start_time_no_tz, end_time_no_tz))
    )
    all_satellite_capture_combinations = session.query(
        Satellite.id.label('satellite_id'),
        ImageOrder.image_type,
        ImageOrder.latitude,
        ImageOrder.longitude
    ).join(ImageOrder, exists_condition).distinct().subquery()

    blocks_to_process = retrieve_and_lock_unprocessed_blocks_for_processing(
        start_time, end_time,
        CaptureProcessingBlock,
        partition_column_names=[
            CaptureProcessingBlock.satellite_id,
            CaptureProcessingBlock.image_type,
            CaptureProcessingBlock.latitude,
            CaptureProcessingBlock.longitude
        ],
        valid_partition_values_subquery=all_satellite_capture_combinations
    )
    with loky.ProcessPoolExecutor() as executor:
        serializable_blocks = [
            SerializableCaptureProcessingBlock(
                id=block.id,
                satellite_id=block.satellite_id,
                image_type=block.image_type,
                latitude=block.latitude,
                longitude=block.longitude,
                time_range=block.time_range
            ) for block in blocks_to_process
        ]
        result_set = executor.map(calculate_capture_opportunities, serializable_blocks)
        processed_block_ids = []
        for block_id, opportunities in result_set:
            capture_opportunities = [
                CaptureOpportunity(
                    asset_id=opportunity.asset_id,
                    image_type=opportunity.image_type,
                    latitude=opportunity.latitude,
                    longitude=opportunity.longitude,
                    start_time=opportunity.start_time,
                    duration=opportunity.duration
                ) for opportunity in opportunities
            ]
            session.add_all(capture_opportunities)
            processed_block_ids.append(block_id)

    session.query(CaptureProcessingBlock).filter(
        CaptureProcessingBlock.id.in_(processed_block_ids)
    ).update(
        {CaptureProcessingBlock.status: 'processed'},
        synchronize_session=False
    )
    session.commit()
    session.rollback() # just making extra sure all locks are released

    
def calculate_capture_opportunities(block):
    session = get_db_session()
    capture_opportunities = []
    state_generators = dict() # satellite_id -> satellite_state_generator
    # Find and insert all eclipse events that occur within the time range of the processing block
    if block.satellite_id not in state_generators:
        satellite = session.query(Satellite).filter_by(id=block.satellite_id).first()
        state_generators[block.satellite_id] = SatelliteStateGenerator(satellite, precision=timedelta(seconds=10))
    
    state_generator = state_generators[block.satellite_id]
    event_time_ranges = state_generator.capture_events(
        block.time_range.lower,
        block.time_range.upper,
        block
    )

    # merge events that either overlap, or are contiguous, and create the appropriate events
    for event_start, event_end in event_time_ranges:
        event_start = event_start.utc_datetime().replace(tzinfo=None) # remove time zone info to compare with utc_time_range column which is tsrange type (doesn't have timezone info)
        event_end = event_end.utc_datetime().replace(tzinfo=None)

        merged_events = session.query(CaptureOpportunity).filter(
            CaptureOpportunity.asset_id == block.satellite_id,
            CaptureOpportunity.image_type == block.image_type,
            CaptureOpportunity.latitude == block.latitude,
            CaptureOpportunity.longitude == block.longitude,
            or_(
                CaptureOpportunity.utc_time_range.op('&&')(func.tsrange(event_start, event_end)), # if the eclipse overlaps with our eclipse
                func.lower(CaptureOpportunity.utc_time_range) == event_end, # if the eclipse starts where our eclipse ends
                func.upper(CaptureOpportunity.utc_time_range) == event_start # if the eclipse ends where our eclipse starts
            )
        ).all()

        if merged_events:
            min_overlapping_start = min([event.utc_time_range.lower for event in merged_events])
            max_overlapping_end = max([event.utc_time_range.upper for event in merged_events])
            # update capture opportunity start and end to encompass all continuous/overlapping eclipses
            event_start = min(event_start, min_overlapping_start)
            event_end = max(event_end, max_overlapping_end) 

        # first delete overlapping events
        for event in merged_events:
            session.delete(event)
        # then add the event encompassing them all
        capture_opportunities.append(SerializableCaptureOpportunity(
            asset_id=block.satellite_id,
            image_type=block.image_type,
            latitude=block.latitude,
            longitude=block.longitude,
            start_time=event_start,
            duration=event_end - event_start
        ))
    return block.id, capture_opportunities