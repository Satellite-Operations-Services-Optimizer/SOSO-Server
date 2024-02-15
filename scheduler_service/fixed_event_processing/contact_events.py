from datetime import datetime, timedelta
from tokenize import String
from skyfield.api import load, Topos, EarthSatellite
from sqlalchemy import func, or_
from app_config import get_db_session
from app_config.database.mapping import ContactProcessingBlock, ContactEvent, Satellite, GroundStation
from .utils import retrieve_and_lock_unprocessed_blocks_for_processing
from ..satellite_state.state_generator import SatelliteStateGenerator

def ensure_contact_events_populated(start_time: datetime, end_time: datetime):
    session = get_db_session()
    all_satellite_groundstation_combinations_subquery = session.query(
        Satellite.id.label("satellite_id"),
        GroundStation.id.label("groundstation_id")
    ).subquery()
    blocks_to_process = retrieve_and_lock_unprocessed_blocks_for_processing(
        start_time, end_time,
        ContactProcessingBlock,
        partition_columns=[
            ContactProcessingBlock.satellite_id,
            ContactProcessingBlock.groundstation_id
        ],
        valid_partition_values_subquery=all_satellite_groundstation_combinations_subquery
    )

    contact_events = []
    state_generators = dict() # satellite_id -> satellite_state_generator
    groundstations = dict() # groundstation_id -> groundstation
    for block in blocks_to_process:
        # Find and insert all eclipse events that occur within the time range of the processing block
        if block.satellite_id not in state_generators:
            satellite = session.query(Satellite).filter_by(id=block.satellite_id).first()
            state_generators[block.satellite_id] = SatelliteStateGenerator(satellite)
        if block.groundstation_id not in groundstations:
            groundstation = session.query(GroundStation).filter_by(id=block.groundstation_id).first()
            groundstations[block.groundstation_id] = groundstation
        
        state_generator = state_generators[block.satellite_id]
        event_time_ranges = state_generator.contact_events(block.time_range.lower, block.time_range.upper, groundstations[block.groundstation_id])

        # merge events that either overlap, or are contiguous, and create the appropriate events
        for event_start, event_end in event_time_ranges:
            event_start = event_start.utc_datetime().replace(tzinfo=None) # remove time zone info to compare with utc_time_range column which is tsrange type (doesn't have timezone info)
            event_end = event_end.utc_datetime().replace(tzinfo=None)

            merged_events = session.query(ContactEvent).filter(
                ContactEvent.asset_id == block.satellite_id,
                ContactEvent.groundstation_id == block.groundstation_id,
                or_(
                    ContactEvent.utc_time_range.op('&&')(func.tsrange(event_start, event_end)), # if the eclipse overlaps with our eclipse
                    func.lower(ContactEvent.utc_time_range) == event_end, # if the eclipse starts where our eclipse ends
                    func.upper(ContactEvent.utc_time_range) == event_start # if the eclipse ends where our eclipse starts
                )
            ).all()

            if merged_events:
                min_overlapping_start = min([eclipse.utc_time_range.lower for eclipse in merged_events])
                max_overlapping_end = max([eclipse.utc_time_range.upper for eclipse in merged_events])
                # update eclipse start and end to encompass all continuous/overlapping eclipses
                event_start = min(event_start, min_overlapping_start)
                event_end = max(event_end, max_overlapping_end) 

            # first delete overlapping events
            for event in merged_events:
                session.delete(event)
            # then add the event encompassing them all
            contact_events.append(ContactEvent(
                asset_id=block.satellite_id,
                groundstation_id=block.groundstation_id,
                start_time=event_start,
                duration=event_end - event_start,
            ))
    
    session.add_all(contact_events)
    # update blocks_to_proces state to 'processed' using batch update
    for block in blocks_to_process:
        block.status = 'processed'
    session.commit() # releases lock on processing blocks
        

def contact_update(start_time: datetime, end_time: datetime, satellite):
    """
    
    """
    access_points = {}

    while start_time < end_time:
        
        current_time_skyfield = load.timescale().utc(start_time.year, start_time.month, start_time.day, start_time.hour, start_time.minute, start_time.second)
        session = get_db_session()
        ground_stations_list = session.query(GroundStation).all()
        satellite_access = {ground_station.name: None for ground_station in ground_stations_list}  

        for ground_station in ground_stations_list:
            if _is_in_contact(satellite, ground_station, current_time_skyfield):
                # Check if the ground station is not in use by any other satellite at the current time
                if satellite_access[ground_station.name] is None:
                    if ground_station.name not in access_points:
                        access_points[ground_station.name] = {
                            "Access Timestamp Start": [],
                            "Access Timestamp End": [],
                            "Satellite Name": []  # Initialize the 'Satellite Name' list
                        }
                    else:
                        # Initialize the 'Satellite Name' list if it doesn't exist
                        if "Satellite Name" not in access_points[ground_station.name]:
                            access_points[ground_station.name]["Satellite Name"] = []
                    while start_time < end_time:
                        start_time += timedelta(minutes=1)
                        if not _is_in_contact(satellite, ground_station, current_time_skyfield):
                            break
                    access_points[ground_station.name]["Access Timestamp End"].append(start_time.strftime('%Y-%m-%d %H:%M:%S'))
                    access_points[ground_station.name]["Satellite Name"].append(satellite.name)  # Store the satellite name accessing the ground station
                    satellite_access[ground_station.name] = satellite.name  # Mark the ground station as in use by the current satellite
                else:
                    start_time += timedelta(minutes=1)
            else:
                start_time += timedelta(minutes=1)
                # Reset ground station access if the satellite moves out of range
                for gs in satellite_access.keys():
                    if satellite_access[gs] == satellite.name:
                        satellite_access[gs] = None
    return access_points


def _is_in_contact(satellite, ground_station, time):
    ground_station_topos = Topos(ground_station.latitude, ground_station.longitude)
    relative_position = (satellite - ground_station_topos).at(time)
    elevation_angle = relative_position.altaz()[0]
    return elevation_angle.degrees > ground_station.mask

class Stub:
    gs_name: String
    contact: String
    duration: datetime
    loss_of_signal: datetime

    def __innit__(self, gs_name, contact, duration, loss_of_signal):
        self.gs_name=gs_name
        self.contact=contact
        self.duration=duration
        self.duration=loss_of_signal
        
