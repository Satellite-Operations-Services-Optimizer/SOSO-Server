from datetime import datetime
from app_config import get_db_session
from app_config.database.mapping import ContactProcessingBlock, ContactOpportunity, Satellite, GroundStation
from utils import retrieve_and_lock_unprocessed_blocks_for_processing
from ..satellite_state.state_generator import SatelliteStateGenerator

def ensure_contact_opportunities_populated(start_time: datetime, end_time: datetime):
    session = get_db_session()
    blocks_to_process = retrieve_and_lock_unprocessed_blocks_for_processing(
        start_time, end_time,
        ContactProcessingBlock,
        partition_columns=[
            ContactProcessingBlock.satellite_id,
            ContactProcessingBlock.groundstation_id
        ]
    )
    # add, and lock, blocks for satellite/gs combinations that don't any have blocks in this range, or at all, yet (just find all valid partition key values that are not included in the retrieved blocks_to_process)

    contacts = []
    state_generators = dict() # satellite_id -> satellite_state_generator
    groundstations = dict()
    for block in blocks_to_process:
        # Find and insert all eclipse events that occur within the time range of the processing block
        if block.satellite_id not in state_generators:
            satellite = session.query(Satellite).get(block.satellite_id)
            state_generators[block.satellite_id] = SatelliteStateGenerator(satellite)
        if block.groundstation_id not in groundstations
        