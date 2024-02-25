from datetime import datetime
from scheduler_service.event_processing.utils import retrieve_and_lock_unprocessed_blocks_for_processing
from scheduler_service.satellite_state.state_generator import SatelliteStateGenerator
from app_config.database.mapping import Satellite, CaptureProcessingBlock, CaptureOpportunity, ScheduleRequest, ImageOrder
from app_config import get_db_session
from sqlalchemy import func, or_, distinct, exists, tuple_
from datetime import datetime

def ensure_capture_opportunities_populated(start_time: datetime, end_time: datetime):
    session = get_db_session()

    exists_condition = exists().where(
        ScheduleRequest.schedule_id == ImageOrder.schedule_id,
        ScheduleRequest.order_id == ImageOrder.id,
        ScheduleRequest.utc_window_time_range.op('&&')(func.tsrange(start_time, end_time))
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

    capture_opportunities = []
    state_generators = dict() # satellite_id -> satellite_state_generator
    for block in blocks_to_process:
        # Find and insert all eclipse events that occur within the time range of the processing block
        if block.satellite_id not in state_generators:
            satellite = session.query(Satellite).filter_by(id=block.satellite_id).first()
            state_generators[block.satellite_id] = SatelliteStateGenerator(satellite)
        
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
            capture_opportunities.append(CaptureOpportunity(
                asset_id=block.satellite_id,
                image_type=block.image_type,
                latitude=block.latitude,
                longitude=block.longitude,
                start_time=event_start,
                duration=event_end - event_start
            ))
    
    session.add_all(capture_opportunities)
    # update blocks_to_proces state to 'processed' using batch update
    for block in blocks_to_process:
        block.status = 'processed'
    session.commit() # releases lock on processing blocks