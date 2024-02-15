from pytest import Session
from sqlalchemy import desc, func
from app_config.database.mapping import Satellite, GroundStation, ScheduledMaintenance, SatelliteOutage, StateCheckpoint
from app_config import get_db_session
from skyfield.api import EarthSatellite, load, Topos
from skyfield.timelib import Timescale, Time
from skyfield.searchlib import find_discrete
from datetime import datetime, timedelta, timezone
from constants import EARTH_RADIUS, get_ephemeris
from typing import Optional, Union
from dataclasses import dataclass, InitVar
from pydantic import BaseModel
import numpy as np
from math import atan, degrees
from skyfield.api import Topos

# This class extends the database table 'satellite'
class SatelliteStateGenerator:
    def __init__(self, db_satellite: Satellite):
        self._db_satellite = db_satellite

    def state_at(self, time: Union[datetime, Time]):
        """
        Get the state of the satellite at the provided time
        """
        # get the skyfield EarthSatellite object
        satellite = self._get_skyfield_satellite() 

        datetime_time = self._ensure_datetime(time)
        skyfield_time = self._ensure_skyfield_time(time)
        position = satellite.at(skyfield_time).position.km
        subpoint = satellite.at(skyfield_time).subpoint()
        latitude = subpoint.latitude.degrees
        longitude = subpoint.longitude.degrees

        # Calculate altitude from position data
        semi_major_axis_km = satellite.model.a * EARTH_RADIUS
        altitude = semi_major_axis_km - EARTH_RADIUS # The constant comes from ./constants.py file

        is_sunlit = True if self.is_sunlit(skyfield_time) else False
        return SatelliteState(
            satellite_id=self._db_satellite.id,
            time=datetime_time,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            is_sunlit=is_sunlit
        )        

    def can_observe(self, latitude: float, longitude: float, time: Union[datetime, Time]):
        """
        Check if the satellite can be observed from the provided latitude and longitude at the provided time
        """
        time = self._ensure_skyfield_time(time)
        satellite = self._get_skyfield_satellite()
        ephemeris = get_ephemeris()

        observer = Topos(latitude, longitude)
        return satellite.at(time).is_above_horizon(observer, ephemeris)
    
    def is_in_contact_with(self, groundstation: GroundStation, time: Union[datetime, Time]):
        time = self._ensure_skyfield_time(time)

        satellite = self._get_skyfield_satellite() 
        ground_station_topos = Topos(groundstation.latitude, groundstation.longitude)
        relative_position = (satellite - ground_station_topos).at(time)
        elevation_angle = relative_position.altaz()[0]
        return elevation_angle.degrees > groundstation.send_mask

    def is_sunlit(self, time: Time):
        skyfield_satellite = self._get_skyfield_satellite()
        ephemeris = get_ephemeris()

        is_sunlit = skyfield_satellite.at(time).is_sunlit(ephemeris)
        return is_sunlit
    
    def eclipse_events(self, start_time: Union[datetime, Time], end_time: Union[datetime, Time]):
        """
        Get the eclipse events for the satellite between `start_time` and `end_time`
        """
        eclipse_events = []

        start_time = self._ensure_skyfield_time(start_time)
        end_time = self._ensure_skyfield_time(end_time)

        step_time_minutes = 1
        def is_sunlit_wrapper(time: Time):
            return self.is_sunlit(time)
        is_sunlit_wrapper.step_days = step_time_minutes / (24 * 60) # convert minutes to days

        change_times, sunlit_values = find_discrete(start_time, end_time, is_sunlit_wrapper)
        prev_time, prev_sunlit = start_time, self.is_sunlit(start_time)
        for time, is_sunlit in zip(change_times, sunlit_values):
            if not prev_sunlit and is_sunlit:
                eclipse_events.append((prev_time, time))
            prev_time = time
            prev_sunlit = is_sunlit

        if not prev_sunlit and prev_time.tt < end_time.tt:
            eclipse_events.append((prev_time, end_time))

        return eclipse_events
    
    def contact_events(self, start_time: Union[datetime, Time], end_time: Union[datetime, Time], groundstation: GroundStation):
        """
        Get the contact events between the satellite and the groundstation between `start_time` and `end_time`
        """
        contact_events = []

        start_time = self._ensure_skyfield_time(start_time)
        end_time = self._ensure_skyfield_time(end_time)

        satellite = self._get_skyfield_satellite()
        groundstation_topos = Topos(groundstation.latitude, groundstation.longitude)
        change_times, contact_values = satellite.find_events(groundstation_topos, start_time, end_time, altitude_degrees=groundstation.send_mask)

        # def is_in_contact_wrapper(time: Time):
        #     return self.is_in_contact_with(groundstation, time)
        # is_in_contact_wrapper.step_days = 1 / (24 * 60) # convert minutes to days
        # change_times, contact_values = find_discrete(start_time, end_time, is_in_contact_wrapper)

        event_names = ('rise', 'culminate', 'set')
        prev_rise_time = start_time
        for time, event in zip(change_times, contact_values):
            if event_names[event] == 'rise':
                prev_rise_time = time
            elif event_names[event] == 'set':
                contact_events.append((prev_rise_time, time))

        return contact_events
    
    def observation_events(self, start_time: Union[datetime, Time], end_time: Union[datetime, Time], latitude: float, longitude: float):
        """
        Get the events between `start_time` and `end_time` when the provided latitude and longitude is in the field of view of the satellite.
        """

        start_time = self._ensure_skyfield_time(start_time)
        end_time = self._ensure_skyfield_time(end_time)

        satellite = self._get_skyfield_satellite()
        observer = Topos(latitude, longitude)
        change_times, is_visible_values = satellite.find_events(observer, start_time, end_time, altitude_degrees=0)

        prev_time, prev_visible = start_time, self.can_observe(latitude, longitude, start_time)
        observation_events = []
        for time, is_visible in zip(change_times, is_visible_values):
            if not prev_visible and is_visible:
                observation_events.append((prev_time, time))
            prev_time = time
            prev_visible = is_visible

        if not prev_visible and prev_time.tt < end_time.tt:
            observation_events.append((prev_time, end_time))

        return observation_events

    
    def stream(self, reference_time: Optional[datetime] = None):
        time_offset = reference_time - datetime.now() if reference_time else timedelta(seconds=0)
        ts = self._get_timescale()
        while True:
            yield self.state_at(datetime.now() + time_offset)


    def track(self, start_time: Union[datetime, Time], end_time: Union[datetime, Time], time_delta: timedelta=timedelta(minutes=1)):
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

        line1 = self._db_satellite.tle["line1"]
        line2 = self._db_satellite.tle["line2"]
        name = self._db_satellite.name
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
    
    def _ensure_datetime(self, time: Union[datetime, Time]) -> datetime:
        if isinstance(time, datetime):
            return time
        return time.utc_datetime()
    


class SatelliteState(BaseModel):
    satellite_id: int
    time: datetime
    latitude: float
    longitude: float
    altitude: float
    is_sunlit: bool

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y:%m:%d %H:%M')
        }