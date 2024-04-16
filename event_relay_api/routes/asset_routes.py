from fastapi import APIRouter, File, UploadFile
import json
from fastapi.encoders import jsonable_encoder
from models.asset_creation import GroundStationCreationRequest, SatelliteCreationRequest
from helpers.asset_helper import add_satellite
from helpers.asset_helper import add_satellite
from helpers.miscellaneous_helper import tle_txt_to_json_converter
import logging
from fastapi import HTTPException
from app_config import get_db_session
from app_config.database.mapping import Satellite, GroundStation

logger = logging.getLogger(__name__)
router = APIRouter()

#ground_station endpoints
@router.get("/groundstations")
async def get_all_ground_stations(): 
    session = get_db_session()
    ground_stations = session.query(GroundStation).all()
    return jsonable_encoder(ground_stations)

@router.get("/groundstations/{id}", response_model=GroundStationCreationRequest)
async def get_ground_station(id):
    session = get_db_session()
    ground_station = session.query(GroundStation).filter_by(id=id).first()
    if not ground_station:
        raise HTTPException(404, detail="Groundstation with id={id} does not exist.")
    return jsonable_encoder(ground_station)

@router.post("/groundstations/create")
async def new_ground_station(ground_station: GroundStationCreationRequest):
    session = get_db_session()
    new_ground_station = GroundStation(**ground_station.model_dump())
    session.add(new_ground_station)
    session.commit()
    session.refresh(new_ground_station)
    return new_ground_station.id

#satellite end points
@router.get("/satellites")
async def get_satellites():
    session = get_db_session()
    satellites = session.query(Satellite).all()
    return jsonable_encoder(satellites)

@router.get("/satellites/{id}")
async def get_ground_station(id):
    session = get_db_session()
    satellite = session.query(Satellite).filter_by(id=id).first()
    if not satellite:
        raise HTTPException(404, detail="Satellite with id={id} does not exist.")
    return jsonable_encoder(satellite)

@router.post("/satellites/create")
async def new_satellite(tle_file: UploadFile, satellite_form_data: SatelliteCreationRequest):    
    tle_json = tle_file
    if tle_file.filename.endswith(".txt"):
        tle_txt_to_json_converter(tle_file, tle_json)

    new_satellite = json.load(tle_json.file)
    new_satellite_id = add_satellite(new_satellite, tle_json, satellite_form_data)
    return new_satellite_id
