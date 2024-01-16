from fastapi import APIRouter, File, UploadFile
import json
from fastapi.encoders import jsonable_encoder
from models.asset_creation import GroundStationCreationRequest, SatelliteCreationRequest
from helpers.asset_helper import add_satellite, add_ground_station
from models.SatelliteModel import SatelliteCreationRequest
from models.GroundStationModel import GroundStation
#from Models.SatelliteModel import Satellite
from helpers.asset_helper import add_satellite, add_ground_station, get_all_ground_stations, get_all_satellites, get_ground_station_by_id #,modify_ground_station_by_name
#from Models.EventRelayData import EventRelayApiMessage, RequestDetails
#from config import rabbit, ServiceQueues
#from rabbit_wrapper import Publisher
from helpers.miscellaneous_helper import txt_to_json_converter
import logging
from fastapi import HTTPException
from app_config import get_db_session
from app_config.database.mapping import Satellite, GroundStation

logger = logging.getLogger(__name__)
router = APIRouter()

#ground_station endpoints
@router.get("/ground_stations")
async def get_all_ground_stations(): 
    session = get_db_session()
    ground_stations = session.query(GroundStation).all()
    return jsonable_encoder(ground_stations)

@router.get("/{id}/ground_stations", response_model=GroundStationCreationRequest)
async def get_ground_station(id):
    session = get_db_session()
    ground_station = session.query(GroundStation).filter_by(id=id).first()
    if not ground_station:
        raise HTTPException(404, detail="Ground station does not exist.")
    return jsonable_encoder(ground_station)

@router.post("/create_ground_station")
async def new_ground_station(ground_station: GroundStationCreationRequest):
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
    session = get_db_session()
    satellites = session.query(Satellite).all()
    return jsonable_encoder(satellites)
