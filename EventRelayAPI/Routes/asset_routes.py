from fastapi import APIRouter, Body, Depends, File, UploadFile
import json
from fastapi.encoders import jsonable_encoder
from Models.GroundStationModel import GroundStation
from Models.SatelliteModel import Satellite
from Helpers.postgres_helper import add_satellite, add_ground_station, get_all_ground_stations, get_ground_station_by_id #,modify_ground_station_by_name
#from Models.EventRelayData import EventRelayApiMessage, RequestDetails
#from config import rabbit, ServiceQueues
#from rabbit_wrapper import Publisher

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
async def new_satellite(satellite_json: UploadFile = File(...)):    
    
    new_satellite = json.load(satellite_json.file)
    new_satellite_id = add_satellite(new_satellite)
    return new_satellite_id


"""     request = jsonable_encoder(ground_station)

    request_details = RequestDetails(requestType="add-ground-station")

    message = jsonable_encoder(
        EventRelayApiMessage(
            body=request,
            details=request_details
        )
    )

    logger.debug("received request")
    publisher = Publisher(rabbit(), ServiceQueues.IMAGE_MANAGEMENT)
    logger.debug("publisher created")
    publisher.publish_message(message)

    return message """