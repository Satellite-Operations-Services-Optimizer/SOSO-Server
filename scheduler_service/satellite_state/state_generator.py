from pytest import Session
from sqlalchemy import desc
from app_config.database.mapping import Satellite, GroundStation, ScheduledMaintenance, SatelliteOutage, StateCheckpoint
from app_config import get_db_session
from skyfield.api import EarthSatellite, load
from skyfield.timelib import Timescale, Time
from skyfield.searchlib import find_discrete
from datetime import datetime, timedelta
from constants import EARTH_RADIUS, get_ephemeris
from typing import Optional, Union
from dataclasses import dataclass, InitVar
import numpy as np

# This class extends the database table 'satellite'
class SatelliteStateGenerator:
    def __init__(self, db_satellite: Satellite):
        self.db_satellite = db_satellite

    def state_at(self, time: Union[datetime, Time]):
        """
        Get the state of the satellite at the provided time
        """
        # get the skyfield EarthSatellite object
        satellite = self._get_skyfield_satellite() 

        skyfield_time = self._ensure_skyfield_time(time)
        position = satellite.at(skyfield_time).position.km
        subpoint = satellite.at(skyfield_time).subpoint()
        latitude = subpoint.latitude.degrees
        longitude = subpoint.longitude.degrees

        # Calculate altitude from position data
        semi_major_axis_km = satellite.model.a * EARTH_RADIUS
        altitude = semi_major_axis_km - EARTH_RADIUS # The constant comes from ./constants.py file

        # Query to get satellite state
        session = get_db_session()
        satellite_state = session.query(
                StateCheckpoint.state
            ).filter(
                StateCheckpoint.checkpoint_time <= time, asset_id=self.db_satellite.id, asset_type="satellite", schedule_id=0
            ).order_by(
                StateCheckpoint.checkpoint_time, desc=True
            ).limit(1)

        is_sunlit = self.is_sunlit(skyfield_time)
        return SatelliteState(
            satellite_id=self.db_satellite.id,
            time=skyfield_time.utc_datetime(),
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            is_sunlit=is_sunlit,
            power_draw=satellite_state.power_draw,
            storage_util=satellite_state.power_draw,
            in_maintenance=self._satellite_maintainence_at,
            in_outage=self._satellite_outage_at
        )        

    def _satellite_maintainence_at(self, time: Union[datetime, Time]):
        """
        Checks to see if there is a scheduled maintenance of the satellite at the provided time
        """
        time = self._ensure_datetime()
        session = get_db_session()
        satellite_maintenance = session.query(
            ScheduledMaintenance
        ).filter(
            ScheduledMaintenance.time_range.op('&&')(time),
            schedule_id=0, 
            asset_id=self.db_satellite.id
        ).first()

        if satellite_maintenance is None:
            return False
        else:
            return True
        
    def _satellite_outage_at(self, time: Union[datetime, Time]):
        """
        Checks to see if the provided satellite has an outage at the provided time
        """
        time = self._ensure_datetime()
        session = get_db_session()
        satellite_outage = session.query(
            SatelliteOutage
        ).filter(
            SatelliteOutage.time_range.op('&&')(time),
            schedule_id=0, 
            asset_id=self.db_satellite.id
        ).first()
        
        if satellite_outage is None:
            return False
        else:
            return True
    
    def groundstation_visibility(self, groundstation: GroundStation, time: Union[datetime, Time]):
        time = self._ensure_skyfield_time(time)

        return 


    def is_sunlit(self, time: Time):
        skyfield_satellite = self._get_skyfield_satellite()
        ephemeris = get_ephemeris()

        is_sunlit = skyfield_satellite.at(time).is_sunlit(ephemeris)
        return True if is_sunlit else False
    
    def eclipse_events(self, start_time: Union[datetime, Time], end_time: Union[datetime, Time]):
        """
        Get the eclipse events for the satellite between `start_time` and `end_time`
        """
        start_time = self._ensure_skyfield_time(start_time)
        end_time = self._ensure_skyfield_time(end_time)

        eclipses = []
        change_times, sunlit_values = find_discrete(start_time, end_time, self.is_sunlit)

        prev_time, prev_sunlit = start_time, self.is_sunlit(start_time)
        for time, is_sunlit in zip(change_times, sunlit_values):
            if not prev_sunlit and is_sunlit:
                eclipses.append((prev_time, time))
            prev_time = time
            prev_sunlit = is_sunlit

        if not prev_sunlit and prev_time < end_time:
            eclipses.append((prev_time, end_time))

        return eclipses
    
    def stream(self, reference_time: Optional[datetime] = None):
        time_offset = reference_time - datetime.now() if reference_time else timedelta(seconds=0)
        ts = self._get_timescale()
        while True:
            yield self.state_at(datetime.now() + time_offset)


    def track(self, start_time: Union[datetime, Time], end_time: Union[datetime, Time], time_delta: timedelta):
        """
        This is a generator that iterates through the states of the satelite from `start_time` to `end_time` at intervals of `time_delta`
        """
        start_time = self._ensure_skyfield_time(start_time)
        end_time = self._ensure_skyfield_time(end_time)

        ts = self._get_timescale()
        current_time = start_time # Compare Julian dates
        while current_time.tt < end_time.tt:
            yield self.state_at(current_time)
            current_time = ts.utc(current_time.utc_datetime() + time_delta)

    _skyfield_satellite: Optional[EarthSatellite] = None
    def _get_skyfield_satellite(self):
        if self._skyfield_satellite is not None:
            return self._skyfield_satellite

        line1 = self.db_satellite.tle["line1"]
        line2 = self.db_satellite.tle["line2"]
        name = self.db_satellite.name
        self._skyfield_satellite = EarthSatellite(line1, line2, name, self._get_timescale())
        return self._skyfield_satellite

    _timescale: Optional[Timescale] = None
    def _get_timescale(self):
        if self._timescale is None:
            self._timescale = load.timescale()
        return self._timescale

    def _ensure_skyfield_time(self, time: Union[datetime, Time]) -> Time:
        if isinstance(time, Time):
            return time

        # convert the datetime object to a skyfield Time object
        ts = self._get_timescale()
        skyfield_time = ts.utc(time.year, time.month, time.day, time.hour, time.minute, time.second)
        return skyfield_time
    
    def _ensure_datetime(self, time: Union[datetime, Time]):
        if isinstance(time, datetime):
            return time
        
        return time.utc.datetime()


@dataclass
class SatelliteState:
    time: InitVar[datetime]
    latitude: float
    longitude: float
    altitude: float
    is_sunlit: bool
    power_draw: float
    storage_util: float
    in_maintenance: bool
    in_outage: bool

    def __post_init__(self, time: datetime):
        self.time = time.strftime('%Y:%m:%d %H:%M')

    def __str__(self):
        return f"{{time: {self.time}, latitude: {self.latitude}, longitude: {self.longitude}, altitude: {self.altitude}, is_sunlit: {self.is_sunlit}, fov: {self.fov}}}"
