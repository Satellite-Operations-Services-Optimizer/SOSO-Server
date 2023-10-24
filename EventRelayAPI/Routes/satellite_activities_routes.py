from fastapi import APIRouter, Body, Depends
from fastapi.encoders import jsonable_encoder
from dotenv import dotenv_values
from Helpers.RequestValidator import validate_request_schema
from Models.ActivityRequestModel import ActivityRequest
from Models.EventRelayData import EventRelayApiMessage
from Services.publisher import Publisher

import logging

config = dotenv_values()
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/maintenance-activity-requests")
async def handle_request(maintenance_request: ActivityRequest = Depends(lambda request_data=Body(...): validate_request_schema(request_data, ActivityRequest))):
    
    request = jsonable_encoder(maintenance_request)

    message = jsonable_encoder(
        EventRelayApiMessage(
            body=request
        )
    )

    publisher = Publisher("SatelliteActivitiesServiceEventData")
    
    publisher.publish_message(message)

    return message
    
