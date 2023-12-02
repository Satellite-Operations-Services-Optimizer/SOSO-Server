from fastapi import APIRouter, Body, Depends, File, UploadFile
import json
from fastapi.encoders import jsonable_encoder
from Models.SatelliteModel import SatelliteCreationRequest
from Models.GroundStationModel import GroundStation
#from Models.SatelliteModel import Satellite
from Helpers.asset_helper import add_satellite, add_ground_station, get_all_ground_stations, get_all_satellites, get_ground_station_by_id #,modify_ground_station_by_name
#from Models.EventRelayData import EventRelayApiMessage, RequestDetails
#from config import rabbit, ServiceQueues
#from rabbit_wrapper import Publisher
from Helpers.utils import txt_to_json_converter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

#ground_station endpoints
@router.get("/ground_stations")
async def get_ground_stations(): 
    return get_all_ground_stations()

@router.get("/ground_stations/{id}", response_model=GroundStation)
async def get_ground_station(id):
    return get_ground_station_by_id(id)

@router.post("/create_ground_station")
async def new_ground_station(ground_station: GroundStation):
    new_ground_station = ground_station.model_dump()
    new_ground_station_id = add_ground_station(new_ground_station)
    return new_ground_station_id

""" @router.put("/ground_stations/{name}")
async def modify_ground_station(name):
    return modify_ground_station_by_name(name) """


#satellite end points
@router.post("/create_satellite")
async def new_satellite(tle_file: UploadFile = File(...), 
                        satellite_form_data = SatelliteCreationRequest):    
    
    tle_json = tle_file
    if tle_file.filename.endswith(".txt"):
        txt_to_json_converter(tle_file, tle_json)

    new_satellite = json.load(tle_json.file)
    new_satellite_id = add_satellite(new_satellite, tle_json, satellite_form_data)
    return new_satellite_id

@router.get("/satellites")
async def get_satellites():
    return get_all_satellites()
