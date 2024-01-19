from fastapi import APIRouter, Body, Depends
from fastapi.encoders import jsonable_encoder
from fastapi_pagination import Page
from helpers.request_validation_helper import validate_request_schema
from models.ImageRequestModel import ImageRequest
from models.EventRelayData import EventRelayApiMessage, RequestDetails
from app_config import rabbit, ServiceQueues
from rabbit_wrapper import Publisher
from app_config import get_db_session
from app_config.database.mapping import ImageOrder
from helpers.request_validation_helper import validate_request_schema
from models.ImageRequestModel import ImageRequest
from models.EventRelayData import EventRelayApiMessage, RequestDetails
from app_config import rabbit, ServiceQueues
from rabbit_wrapper import Publisher
from app_config.database.mapping import ImageOrder
from app_config import get_db_session
import logging
from fastapi import Query    

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/orders/create")
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

    
@router.get("/orders")
async def get_all_image_orders(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1), all: bool = Query(False)):
    session = get_db_session()
    query = session.query(ImageOrder)
    if not all:
        query.limit(per_page).offset((page - 1) * per_page)
    return query.all()

