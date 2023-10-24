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


# def validate_request_schema(image_request_data: dict = Body(...)) -> ImageRequest:
#     try:
#         ImageRequest.model_validate(image_request_data)
#         return ImageRequest(**image_request_data) 
#     except ValidationError:
#         raise HttpErrorHandler(status_code=400, detail="Invalid Payload Schema")

# def validate_request_schema(request_data: dict = Body(...), model_type: Type[BaseModel] = None) -> BaseModel:
#     try:
#         model_type.model_validate(request_data)
#         return model_type(**request_data) 
#     except ValidationError:
#         raise HttpErrorHandler(status_code=400, detail="Invalid Payload Schema")

# def get_validator(model_type: Type[BaseModel]) -> Callable:
#     def _validator(request_data: dict = Body(...)) -> BaseModel:
#         return validate_request_schema(request_data=request_data, model_type=model_type)
#     return _validator


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
    
