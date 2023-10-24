from fastapi import APIRouter, Body, Depends
from fastapi.encoders import jsonable_encoder
from dotenv import dotenv_values
from datetime import datetime
from Helpers.ExceptionHandler import HttpErrorHandler
from Models.QueueModel import ImageRequest, RequestDetails
from Models.ServerDataConsumerEventData import Message
from Services.publisher import Publisher
from pydantic import ValidationError
import logging

config = dotenv_values()
logger = logging.getLogger(__name__)
router = APIRouter()


def validate_request_schema(image_request_data: dict = Body(...)) -> ImageRequest:
    try:
        ImageRequest.model_validate(image_request_data)
        return ImageRequest(**image_request_data) 
    except ValidationError:
        raise HttpErrorHandler(status_code=400, detail="Invalid Payload Schema")


@router.post("/image_request")
async def handle_request(image_request: ImageRequest = Depends(validate_request_schema)):
    request = jsonable_encoder(image_request)

    request_details = RequestDetails(requestTime=datetime.now())

    message = jsonable_encoder(
        Message(
            body=request,
            details=request_details
        )
    )

    publisher = Publisher("ImageManagementServiceEventData")
    
    publisher.publish_message(message)

    return message
    
