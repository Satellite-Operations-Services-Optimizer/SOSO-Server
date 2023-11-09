from fastapi import APIRouter, Body, Depends
from fastapi.encoders import jsonable_encoder
from helpers.RequestValidator import validate_request_schema
from models.ImageRequestModel import ImageRequest
from models.EventRelayData import EventRelayApiMessage
from config import rabbit, ServiceQueues
from rabbit_wrapper import Publisher

import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/image-requests")
async def handle_request(image_request: ImageRequest = Depends(lambda request_data=Body(...): validate_request_schema(request_data, ImageRequest))):
    request = jsonable_encoder(image_request)

    message = jsonable_encoder(
        EventRelayApiMessage(
            body=request
        )
    )
    logger.debug("received request")
    publisher = Publisher(rabbit(), ServiceQueues.IMAGE_MANAGEMENT)
    logger.debug("publisher created")
    publisher.publish_message(message)

    return message
    
