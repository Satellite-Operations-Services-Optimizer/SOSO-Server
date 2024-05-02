from fastapi import APIRouter, Body, Depends, Query, HTTPException, Response
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
from app_config.database.mapping import ImageOrder, ScheduleRequest, Asset
from app_config import get_db_session
from sqlalchemy import and_
import logging
from datetime import timedelta, datetime
from helpers.queries import create_exposed_schedule_requests_query
from helpers.utils import paginated_response
from typing import List

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/dashBoardOrders")
async def getDashBoardOrders():
    session = get_db_session()
    order_items = session.query(ScheduleRequest).filter(ScheduleRequest.order_type=="imaging" or ScheduleRequest.order_type=="maintenance").order_by(ScheduleRequest.window_start).limit(100).all()
    return order_items

@router.get("/orders")
async def get_all_image_orders(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1), all: bool = Query(False)):
    session = get_db_session()
    query = session.query(
        *ImageOrder.__table__.columns,
        Asset.name.label("asset_name")
    ).join(
        Asset, (ImageOrder.asset_type==Asset.asset_type) & (ImageOrder.asset_id==Asset.id),
        isouter=True
    ).order_by(ImageOrder.window_start)
    total = query.count()
    if not all:
        query = query.limit(per_page).offset((page - 1) * per_page)
    return paginated_response([request._asdict() for request in query.all()], total)

@router.get("/orders/{id}")
async def get_image_order(id):
    session = get_db_session()
    image_order = session.query(
        *ImageOrder.__table__.columns,
        Asset.name.label("asset_name")
    ).join(
        Asset, (ImageOrder.asset_type==Asset.asset_type) & (ImageOrder.asset_id==Asset.id),
        isouter=True
    ).filter_by(id=id).first()
    if not image_order:
        raise HTTPException(404, detail="Image order with id={id} does not exist.")
    return image_order

@router.get("/orders/{id}/requests")
async def get_image_order_requests(id):
    requests = create_exposed_schedule_requests_query().filter(
        and_(
            ScheduleRequest.order_id==id,
            ScheduleRequest.order_type=="imaging"
        )
    )
    return [request._asdict() for request in requests.all()]

@router.post("/orders/{id}/requests/decline")
async def decline_image_order_requests(id):
    session = get_db_session()
    order = session.query(ImageOrder).filter_by(id=id).first()
    if not order:
        raise HTTPException(404, detail="Order does not exist.")
    requests = session.query(ScheduleRequest).filter_by(order_id=order.id, order_type="imaging").all()
    for request in requests:
        TopicPublisher(rabbit(), f"schedule.request.{request.order_type}.decline").publish_message(request.id)
    session.commit()

@router.post("/orders/create")
async def create_order(image_request: ImageRequest = Depends(lambda request_data=Body(...): validate_request_schema(request_data, ImageRequest))):
    number_of_visits = image_request.Recurrence.NumberOfRevisits + 1
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
        window_start=datetime.fromisoformat(image_request.ImageStartTime),
        window_end=datetime.fromisoformat(image_request.ImageEndTime),
        delivery_deadline=datetime.fromisoformat(image_request.DeliveryTime),
        number_of_visits=number_of_visits,
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
