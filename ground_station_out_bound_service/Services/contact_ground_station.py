from fastapi.encoders import jsonable_encoder
import requests
from app_config.database import db_session
from Helpers.data import get_schedule, get_ground_station_request 
from Models.ScheduleModel import satellite_schedule, ground_station_request

def send_satellite_schedule(schedule: satellite_schedule):
    
    gs_url = 'https:localhost:5000/satellite_schedule'
    
    message = jsonable_encoder(schedule)
    
    response = requests.post(gs_url, json= message)
    return response;

def send_ground_station_request(id: int):
    ground_station_request = get_ground_station_request(db_session, id)
    gs_url = 'https:localhost:5000/ground_station_schedule'
    
    message = jsonable_encoder(ground_station_request)
    
    response = requests.post(gs_url, json= message)
    return response;
    

    