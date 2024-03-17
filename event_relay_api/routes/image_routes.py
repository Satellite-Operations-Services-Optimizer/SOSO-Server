from fastapi import APIRouter, Body, Depends, Query, HTTPException
from helpers.request_validation_helper import validate_request_schema
from event_relay_api.models.image_request_model import ImageRequest
from event_relay_api.models.event_relay_data import EventRelayApiMessage, RequestDetails
from app_config import rabbit, ServiceQueues
from rabbit_wrapper import TopicPublisher
from app_config import get_db_session
from app_config.database.mapping import ImageOrder
from helpers.request_validation_helper import validate_request_schema
from event_relay_api.models.image_request_model import ImageRequest
from event_relay_api.models.event_relay_data import EventRelayApiMessage, RequestDetails
from app_config.database.mapping import ImageOrder, ScheduleRequest
from app_config import get_db_session
import logging
from datetime import timedelta, datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/orders")
async def get_all_image_orders(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1), all: bool = Query(False)):
    session = get_db_session()
    query = session.query(ImageOrder)
    if not all:
        query.limit(per_page).offset((page - 1) * per_page)
    return query.all()

@router.get("/orders/{id}")
async def get_maintenance_order(id):
    session = get_db_session()
    image_order = session.query(ImageOrder).filter_by(id=id).first()
    if not image_order:
        raise HTTPException(404, detail="Image order with id={id} does not exist.")
    return image_order

@router.post("/orders/create")
async def create_order(image_request: ImageRequest = Depends(lambda request_data=Body(...): validate_request_schema(request_data, ImageRequest))):
    num_revisits = image_request.Recurrence.NumberOfRevisits or 0
    visits_remaining = num_revisits+1,
    if image_request.Recurrence.Revisit.lower()=="true":
        frequency_amount = image_request.Recurrence.RevisitFrequency
        frequency_unit = image_request.Recurrence.RevisitFrequencyUnits.lower()
        revisit_frequency = timedelta(**{frequency_unit: frequency_amount})
    else:
        revisit_frequency = None
    
    image_order = ImageOrder(
        latitude=image_request.Latitude,
        longitude=image_request.Longitude,
        priority=image_request.Priority,
        image_type=parse_image_type(image_request.ImageType),
        start_time=datetime.fromisoformat(image_request.ImageStartTime),
        end_time=datetime.fromisoformat(image_request.ImageEndTime),
        delivery_deadline=datetime.fromisoformat(image_request.DeliveryTime),
        repeat_count=num_revisits,
        visits_remaining=visits_remaining,
        revisit_frequency=revisit_frequency
    )
    session = get_db_session()
    session.add(image_order)
    session.commit()

    TopicPublisher(rabbit(), f"order.{image_order.order_type}.created").publish_message(image_order.id)
    return image_order.id

    
def parse_image_type(request_image_type):
    type_mappings = {
        'low': 'low',
        'medium': 'medium',
        'high': 'spotlight'
    }
    return type_mappings[request_image_type.lower()]