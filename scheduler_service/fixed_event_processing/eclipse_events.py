from datetime import datetime
from sqlalchemy import func, or_
from app_config import get_db_session
from app_config.database.mapping import EclipseProcessingBlock, SatelliteEclipse, Satellite
from .utils import retrieve_and_lock_unprocessed_blocks_for_processing
from ..satellite_state.state_generator import SatelliteStateGenerator

def ensure_eclipse_events_populated(start_time: datetime, end_time: datetime):
    session = get_db_session()
    blocks_to_process = retrieve_and_lock_unprocessed_blocks_for_processing(
        start_time, end_time,
        EclipseProcessingBlock,
        partition_columns=[EclipseProcessingBlock.satellite_id],
        valid_partition_values_subquery=session.query(Satellite.id.label('satellite_id')).subquery()
    )
    # add, and lock, blocks for satellites that don't any have blocks in this range, or at all, yet (just find all valid partition key values that are not included in the retrieved blocks_to_process)

    eclipses = []
    state_generators = dict() # satellite_id -> satellite_state_generator
    for block in blocks_to_process:
        # Find and insert all eclipse events that occur within the time range of the processing block
        if block.satellite_id not in state_generators:
            satellite = session.query(Satellite).get(block.satellite_id)
            state_generators[block.satellite_id] = SatelliteStateGenerator(satellite)
        
        state_generator = state_generators[block.satellite_id]
        eclipse_time_ranges = state_generator.eclipse_events(block.time_range.lower, block.time_range.upper)

        # merge eclipses in case there are other eclipses that overlap (more specifically are continuous) with you. otherwise, create a new eclipse
        for eclipse_start, eclipse_end in eclipse_time_ranges:
            eclipse_start = eclipse_start.utc_datetime()
            eclipse_end = eclipse_end.utc_datetime()

            overlapping_eclipses = session.query(SatelliteEclipse).filter(
                SatelliteEclipse.asset_id == block.satellite_id,
                or_(
                    func.lower(SatelliteEclipse.utc_time_range) >= eclipse_start,
                    func.upper(SatelliteEclipse.utc_time_range) <= eclipse_end
                )
            ).all()

            # first delete overlapping eclipses
            if overlapping_eclipses:
                min_start = min(eclipse.utc_time_range.lower for eclipse in overlapping_eclipses)
                max_end = max(eclipse.utc_time_range.upper for eclipse in overlapping_eclipses)

                for eclipse in overlapping_eclipses:
                    session.delete(eclipse)

                eclipse_start, eclipse_end = min_start, max_end # update eclipse start and end to encompass all continuous/overlapping eclipses

            # then add the eclipse encompassing them all
            eclipses.append(SatelliteEclipse(
                asset_id=block.satellite_id,
                start_time=eclipse_start,
                duration=eclipse_end - eclipse_start,
            ))
    
    session.add_all(eclipses)
    # update blocks_to_proces state to 'processed' using batch update
    for block in blocks_to_process:
        block.status = 'processed'
    session.commit() # releases lock on processing blocks
        