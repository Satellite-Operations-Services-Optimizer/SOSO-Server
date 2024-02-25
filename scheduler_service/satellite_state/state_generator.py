from pytest import Session
from sqlalchemy import desc, func
from app_config.database.mapping import Satellite, GroundStation, ScheduledMaintenance, SatelliteOutage, StateCheckpoint, ImageOrder
from app_config import get_db_session
from skyfield.api import EarthSatellite, load, Topos
from skyfield.timelib import Timescale, Time
from skyfield.searchlib import find_discrete
from datetime import datetime, timedelta, timezone
from scheduler_service.constants import EARTH_RADIUS, get_ephemeris
from typing import Optional, Union
from dataclasses import dataclass, InitVar
from pydantic import BaseModel
import numpy as np
from math import atan, degrees
from skyfield.api import Topos
from haversine import haversine
from scheduler_service.utils import get_image_dimensions

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

        sunlit_value = self.is_sunlit(skyfield_time)

        try:
            len(skyfield_time) # This will raise a TypeError if skyfield_time represents a single time
        except TypeError:
            return SatelliteState(
                satellite_id=self._db_satellite.id,
                time=datetime_time,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                is_sunlit=sunlit_value
            )

        states = np.empty(len(skyfield_time), dtype=SatelliteState)
        for i in range(len(skyfield_time)):
            states[i] = SatelliteState(
                satellite_id=self._db_satellite.id,
                time=datetime_time[i],
                latitude=latitude[i],
                longitude=longitude[i],
                altitude=altitude,
                is_sunlit=sunlit_value[i]
            )
        
        if len(states) == 1: return states[0]
        return np.array(states)
    
    def can_capture(self, image_order: ImageOrder, time: Union[datetime, Time]):
        """
        Check if the satellite can capture an image of the target at the provided time
        """
        satellite_states = self.state_at(time)
        if type(satellite_states) == list:
            satellite_states = np.array(satellite_states)
        elif not isinstance(satellite_states, np.ndarray):
            satellite_states = np.array([satellite_states])
        
        can_capture_values = np.empty(len(satellite_states), dtype=bool)
        for i, satellite_state in enumerate(satellite_states):
            satellite_position = (satellite_state.latitude, satellite_state.longitude)
            target_latitude, target_longitude = image_order.latitude, image_order.longitude

            distX = haversine((target_latitude, satellite_state.longitude), satellite_position)
            distY = haversine((satellite_state.latitude, target_longitude), satellite_position)

            image_length, image_width = get_image_dimensions(image_order.image_type)

            sat_fov = self._db_satellite.fov_min
            
            image_within_view = distX < (sat_fov - 0.5*image_length) and distY < (sat_fov - 0.5*image_width)
            can_capture_values[i] = image_within_view

        if len(can_capture_values)==1: return can_capture_values[0]
        return can_capture_values
    
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

        if not prev_sunlit and prev_time.tt < end_time.tt and len(change_times) > 0:
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

        event_names = ('rise', 'culminate', 'set')
        prev_rise_time = start_time
        for time, event in zip(change_times, contact_values):
            if event_names[event] == 'rise':
                prev_rise_time = time
            elif event_names[event] == 'set':
                contact_events.append((prev_rise_time, time))

        return contact_events
    
    def capture_events(self, start_time: Union[datetime, Time], end_time: Union[datetime, Time], image_order: ImageOrder):
        """
        Get the events between `start_time` and `end_time` when the provided latitude and longitude is in the field of view of the satellite.
        """
        capture_events = []

        start_time = self._ensure_skyfield_time(start_time)
        end_time = self._ensure_skyfield_time(end_time)

        step_time_minutes = 1
        def can_capture_wrapper(time: Time):
            return self.can_capture(image_order, time)
        can_capture_wrapper.step_days = step_time_minutes / (24 * 60) # convert minutes to days

        change_times, capture_values = self.manual_find_discrete(start_time, end_time, can_capture_wrapper)
        prev_time, prev_can_capture = start_time, self.can_capture(image_order, start_time)
        for time, can_capture in zip(change_times, capture_values):
            if not prev_can_capture and can_capture:
                capture_events.append((prev_time, time))
            prev_time = time
            prev_can_capture = can_capture

        if not prev_can_capture and prev_time.tt < end_time.tt and len(change_times) > 0:
            capture_events.append((prev_time, end_time))

        return capture_events

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
    
    def manual_find_discrete(self, start_time: Time, end_time: Time, function):
        """
        This function is a manual implementation of the skyfield.searchlib.find_discrete() function, as it doesn't seem to work for some cases.
        """
        step_days = timedelta(days=function.step_days)
        # calculate number of steps
        start = self._ensure_datetime(start_time)
        end = self._ensure_datetime(end_time)
        num_steps = int(np.ceil((end - start).total_seconds() / step_days.total_seconds()))

        # Generate an array of times using linspace, ensuring coverage of the entire interval
        ts = self._get_timescale()
        times_to_evaluate = ts.linspace(start_time, end_time, num_steps)

        # detect change points, including the first point
        values = function(times_to_evaluate)
        changes = np.diff(values, prepend=values[0])
        change_indices = np.where(changes != 0)[0]

        change_times = times_to_evaluate[change_indices]
        return change_times, values[change_indices]


class SatelliteState(BaseModel):
    satellite_id: int
    time: datetime
    latitude: float
    longitude: float
    altitude: float
    is_sunlit: bool

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
