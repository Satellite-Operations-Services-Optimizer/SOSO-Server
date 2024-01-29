from fastapi import APIRouter, Body, Depends
from fastapi.encoders import jsonable_encoder
from fastapi_pagination import Page
from helpers.request_validation_helper import validate_request_schema
from event_relay_api.models.image_request_model import ImageRequest
from event_relay_api.models.event_relay_data import EventRelayApiMessage, RequestDetails
from app_config import rabbit, ServiceQueues
from rabbit_wrapper import Publisher
from app_config import get_db_session
from app_config.database.mapping import ImageOrder
from helpers.request_validation_helper import validate_request_schema
from event_relay_api.models.image_request_model import ImageRequest
from event_relay_api.models.event_relay_data import EventRelayApiMessage, RequestDetails
from app_config import rabbit, ServiceQueues
from rabbit_wrapper import Publisher
from app_config.database.mapping import ImageOrder, ScheduleRequest
from app_config import get_db_session
import logging
from fastapi import Query    
from datetime import timedelta, datetime

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/orders/create")
async def handle_request(image_request: ImageRequest = Depends(lambda request_data=Body(...): validate_request_schema(request_data, ImageRequest))):
    session = get_db_session()
    
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

    # Your integration logic starts here
    order_data = image_request.get("OrderData")
    recurrence = order_data.get('Recurrence', {})
    revisit = recurrence.get('Revisit', False)
    number_of_revisits = int(recurrence.get('NumberOfRevisits', 0))
    revisit_frequency = int(recurrence.get('RevisitFrequency', 0))
    revisit_frequency_units = recurrence.get('RevisitFrequencyUnits', 'Days')

    image_start_time = datetime.strptime(order_data['ImageStartTime'], '%Y-%m-%dT%H:%M:%S')
    image_end_time = datetime.strptime(order_data['ImageEndTime'], '%Y-%m-%dT%H:%M:%S')
    delivery_time = datetime.strptime(order_data['DeliveryTime'], '%Y-%m-%dT%H:%M:%S')
    
    duration = image_end_time - image_start_time

    if revisit:
        parent_order = ImageOrder(
            start_time=image_start_time,
            end_time=image_end_time,
            duration=duration,
            delivery_deadline=delivery_time,
            number_of_revisits=number_of_revisits,
            revisit_frequency=revisit_frequency,
            priority=order_data['Priority']
        )

        session.add(parent_order)
        session.commit()

        for i in range(number_of_revisits):
            new_start_time = image_start_time + (i + 1) * timedelta(days=revisit_frequency)
            new_end_time = image_end_time + (i + 1) * timedelta(days=revisit_frequency)
            new_delivery_time = delivery_time + (i + 1) * timedelta(days=revisit_frequency)

            child_order = ScheduleRequest(
                schedule_id=parent_order.id,
                window_start=new_start_time,
                window_end=new_end_time,
                duration=duration,
                delivery_deadline=new_delivery_time
            )

            session.add(child_order)

        session.commit()

    return message

    
@router.get("/orders")
async def get_all_image_orders(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1), all: bool = Query(False)):
    session = get_db_session()
    query = session.query(ImageOrder)
    if not all:
        query.limit(per_page).offset((page - 1) * per_page)
    return query.all()

