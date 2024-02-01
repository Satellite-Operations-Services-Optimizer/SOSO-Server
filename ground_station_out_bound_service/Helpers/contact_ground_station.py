from fastapi.encoders import jsonable_encoder
import requests
from app_config.database.setup import scoped_session
from ground_station_out_bound_service.Helpers.data import get_schedule, get_ground_station_request 
from ground_station_out_bound_service.models.ScheduleModel import satellite_schedule, ground_station_request

def send_satellite_schedule(schedule: satellite_schedule):
    
    gs_url = 'http://localhost:5000/satellite_schedule'
    
    message = jsonable_encoder(schedule)
    
    response = requests.post(gs_url, json= message)
    return response;

def send_ground_station_request(id: int):
    ground_station_request = get_ground_station_request(scoped_session, id)
    gs_url = 'http://localhost:5000/ground_station_schedule'
    
    message = jsonable_encoder(ground_station_request)
    
    response = requests.post(gs_url, json= message)
    return response;
    

    