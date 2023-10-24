from fastapi import APIRouter, Body, Depends
from fastapi.encoders import jsonable_encoder
from dotenv import dotenv_values
from Helpers.RequestValidator import validate_request_schema
from Models.ImageRequestModel import ImageRequest
from Models.EventRelayData import EventRelayApiMessage
from Services.publisher import Publisher

import logging

config = dotenv_values()
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/image_request")
async def handle_request(image_request: ImageRequest = Depends(lambda request_data=Body(...): validate_request_schema(request_data, ImageRequest))):
    request = jsonable_encoder(image_request)

    message = jsonable_encoder(
        EventRelayApiMessage(
            body=request
        )
    )

    publisher = Publisher("ImageManagementServiceEventData")
    
    publisher.publish_message(message)

    return message
    
