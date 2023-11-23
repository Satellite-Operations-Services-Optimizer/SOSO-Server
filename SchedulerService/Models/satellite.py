from config.database import Base
from skyfield.api import EarthSatellite, load
from skyfield.timelib import Timescale, Time
from datetime import datetime, timedelta
from constants import EARTH_RADIUS, get_ephemeris
from typing import Optional, Union
from dataclasses import dataclass
import numpy as np
from math import atan, degrees

# This class extends the database table 'satellite'
Satellite = Base.classes.satellite
class SatelliteStateGenerator:
    _skyfield_satellite: Optional[EarthSatellite] = None
    _timescale: Optional[Timescale] = None
    def __init__(self, db_satellite: Satellite):
        self.db_satellite = db_satellite

    def state_at(self, time: Union[datetime, Time]):
        """
        Get the state of the satellite at the provided time
        """
        # get the skyfield EarthSatellite object
        satellite = self._get_skyfield_satellite() 

        time = self._ensure_skyfield_time(time)
        position = satellite.at(time).position.km
        subpoint = satellite.at(time).subpoint()
        latitude = subpoint.latitude.degrees
        longitude = subpoint.longitude.degrees

        # Calculate altitude from position data
        altitude = np.linalg.norm(position) - EARTH_RADIUS # The constant comes from ./constants.py file

        # Calculate FOV
        fov = degrees(2 * atan(12742 / (2 * (altitude + EARTH_RADIUS)))) # maybe move constants like '12742' to the constants.py file for better formula readability
        
        is_sunlit = self._is_sunlit(time)
        return SatelliteState(
            time=time,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            fov=fov, # TODO: How do we get this value? is it needed?
            is_sunlit=is_sunlit
        )

    def track(self, start_time: Union[datetime, Time], end_time: Union[datetime, Time], time_delta: timedelta):
        """
        This is a generator that iterates through the states of the satelite from `start_time` to `end_time` at intervals of `time_delta`
        """
        ts = self._get_timescale()
        start_time = self._ensure_skyfield_time(start_time)
        end_time = self._ensure_skyfield_time(end_time)

        current_time = start_time# Compare Julian dates
        while current_time.tt < end_time.tt:
            yield self.state_at(current_time)
            current_time = ts.utc(current_time.utc_datetime() + time_delta)

    def _is_sunlit(self, time: Time):
        skyfield_satellite = self._get_skyfield_satellite()
        ephemeris = get_ephemeris()

        is_sunlit = skyfield_satellite.at(time).is_sunlit(ephemeris)
        return is_sunlit
    
    def _get_skyfield_satellite(self):
        if self._skyfield_satellite is not None:
            return self._skyfield_satellite

        line1 = self.db_satellite.tle["line1"]
        line2 = self.db_satellite.tle["line2"]
        name = self.db_satellite.tle["name"]
        self._skyfield_satellite = EarthSatellite(line1, line2, name, self._get_timescale())
        return self._skyfield_satellite

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



@dataclass
class SatelliteState:
    time: Time
    latitude: float
    longitude: float
    altitude: float
    is_sunlit: bool
    fov: float

    def __str__(self):
        return f"{{time: {self.time}, latitude: {self.latitude}, longitude: {self.longitude}, altitude: {self.altitude}, is_sunlit: {self.is_sunlit}, fov: {self.fov}}}"

# This class extends the database table 'ground station'