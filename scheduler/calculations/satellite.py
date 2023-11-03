from sqlalchemy.ext.automap import automap_base
from datetime import datetime, timedelta
from database import engine
from skyfield.api import EarthSatellite, load
from skyfield.timelib import Timescale, Time
from typing import Optional, Union
from dataclasses import dataclass
from .constants import *
from math import atan, degrees
import inject

Base = automap_base()
Base.prepare(engine, reflect=True)

# You can simply just get the satellite class like this:
# Satellite = base.classes.satellite

# but I want to extend the satellite class with some extra functionality,
# so that's why i'm doing what i'm doing below

# This class extends the database table 'satellite'
class Satellite(Base.classes.satellite):
    _earth_satellite: Optional[EarthSatellite] = None
    _timescale: Optional[Timescale] = None
    def state_at(self, time: Union[datetime, Time]):
        """
        Get the state of the satellite at the provided time
        """
        # get the skyfield EarthSatellite object
        satellite = self._get_earth_satellite_obj() 

        # convert the datetime object to a skyfield Time object
        if isinstance(time, datetime):
            sf_time = self._to_skyfield_time(time) 
        else:
            sf_time = time

        position = satellite.at(sf_time).position.km
        subpoint = satellite.at(sf_time).subpoint()
        latitude = subpoint.latitude.degrees
        longitude = subpoint.longitude.degrees

        # Calculate altitude from position data
        altitude = np.linalg.norm(position) - EARTH_RADIUS # The constant comes from ./constants.py file

        # Calculate FOV
        fov = degrees(2 * atan(12742 / (2 * (altitude_current + EARTH_RADIUS)))) # maybe move constants like '12742' to the constants.py file for better formula readability

        return SatelliteState(time, latitude, longitude, altitude, fov)

    def state_trace(self, start_time: Union[datetime, Time], end_time: Union[datetime, Time], time_delta: timedelta):
        """
        This is a generator that iterates through the states of the satelite from `start_time` to `end_time` at intervals of `time_delta`
        """
        ts = self._get_timescale()
        start_time = self._to_skyfield_time(start_time)
        end_time = self._to_skyfield_time(end_time)

        current_time = start_time# Compare Julian dates
        while current_time.tt < end_time.tt:
            yield self.state_at(current_time)
            current_time = ts.utc(current_time.utc_datetime() + time_delta)

    def _get_timescale():
        if self._timescale is None:
            self._timescale = load.timescale()
        return self._timescale

    def _get_earth_satellite_obj():
        if self._earth_satellite is None:
            return _earth_satellite

        line1 = self.two_line_element["line1"]
        line2 = self.two_line_element["line2"]
        name = self.two_line_element["name"]
        self._earth_satellite = EarthSatellite(line1, line2, name, self._get_timescale())
        return self._earth_satellite

    def _to_skyfield_time(self, time: datetime):
        ts = self._get_timescale()
        skyfield_time = ts.utc(time.year, time.month, time.day, time.hour, time.minute, time.second)
        return skyfield_time


@dataclass
class SatelliteState:
    time: datetime
    latitude: float
    longitude: float
    altitude: float
    fov: float
    eclipsed: bool

