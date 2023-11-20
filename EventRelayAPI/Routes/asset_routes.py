from fastapi import APIRouter, Body, Depends
#from fastapi.encoders import jsonable_encoder
from EventRelayAPI.Models.GroundStationModel import GroundStation
from EventRelayAPI.Models.SatelliteModel import Satellite
from Helpers.RequestValidator import validate_request_schema
#from Helpers.postgres_helper import add_satellite, add_ground_station
#from Models.EventRelayData import EventRelayApiMessage, RequestDetails
#from config import rabbit, ServiceQueues
#from rabbit_wrapper import Publisher

import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/create_ground_station")
async def add_ground_station(ground_station: GroundStation = Depends(lambda request_data=Body(...): validate_request_schema(request_data, GroundStation))):
    new_ground_station_id = add_ground_station(**ground_station.model_dump())
    return new_ground_station_id

@router.post("/create_satellite")
async def add_satellite(satellite: Satellite = Depends(lambda request_data=Body(...): validate_request_schema(request_data, Satellite))):    
    return


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