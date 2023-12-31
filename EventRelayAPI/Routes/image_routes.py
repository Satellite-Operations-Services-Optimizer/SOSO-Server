from fastapi import APIRouter, Body, Depends
from fastapi.encoders import jsonable_encoder
from fastapi_pagination import Page
from Helpers.request_validator import validate_request_schema
from Models.ImageRequestModel import ImageRequest
from Models.EventRelayData import EventRelayApiMessage, RequestDetails
from config import rabbit, ServiceQueues
from rabbit_wrapper import Publisher
from Helpers.image_order_utils import get_image_orders
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/image-requests")
async def handle_request(image_request: ImageRequest = Depends(lambda request_data=Body(...): validate_request_schema(request_data, ImageRequest))):
    request = jsonable_encoder(image_request)

    request_details = RequestDetails(requestType="image-order-request")

    message = jsonable_encoder(
        EventRelayApiMessage(
            body=request,
            details=request_details
        )
    )

    logger.debug("received request")
    publisher = Publisher(rabbit(), ServiceQueues.IMAGE_MANAGEMENT)
    logger.debug("publisher created")
    publisher.publish_message(body=message)

    return message

    
@router.get("/image-orders")
async def get_all_image_orders():
    
    imageOrders = get_image_orders();    
    return imageOrders

