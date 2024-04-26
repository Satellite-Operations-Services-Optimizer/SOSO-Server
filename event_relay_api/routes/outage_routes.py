from fastapi import APIRouter, Body, Depends, Query, HTTPException, Response
import logging
from models.activity_request import ActivityRequest, OutageOrderCreationRequest
from helpers.request_validation_helper import validate_request_schema
from models.activity_request import ActivityRequest
from event_relay_api.helpers.request_validation_helper import validate_request_schema
from app_config import get_db_session, rabbit
from app_config.database.mapping import Satellite, GroundStation, ScheduleRequest, Asset, OutageOrder
from datetime import timedelta, datetime
from rabbit_wrapper import TopicPublisher
from typing import List
from helpers.queries import create_exposed_schedule_requests_query
from helpers.utils import paginated_response

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/orders")
async def get_all_outage_orders(response: Response, asset_type: str = Query(None), page: int = Query(1, ge=1), per_page: int = Query(20, ge=1), all: bool = Query(False)):
    session = get_db_session()
    query = session.query(
        *OutageOrder.__table__.columns,
        Asset.name.label("asset_name")
    ).join(
        Asset, (OutageOrder.asset_type==Asset.asset_type) & (OutageOrder.asset_id==Asset.id)
    ).order_by(OutageOrder.window_start)

    if asset_type:
        query = query.filter(OutageOrder.asset_type==asset_type)
    total = query.count()
    if not all:
        query = query.limit(per_page).offset((page - 1) * per_page)
    return paginated_response([request._asdict() for request in query.all()], total)

@router.get("/orders/{id}")
async def get_outage_order(id: int):
    session = get_db_session()
    outage_order = session.query(OutageOrder).filter_by(id=id).first()
    if not outage_order:
        raise HTTPException(404, detail=f"Outage order with id={id} does not exist.")
    return outage_order

@router.get("/orders/{id}/requests")
async def get_image_order_requests(id):
    requests = create_exposed_schedule_requests_query().filter(ScheduleRequest.order_id==id & ScheduleRequest.order_type=="outage")
    return [request._asdict() for request in requests.all()]

@router.post("/orders/{id}/requests/decline")
async def decline_outage_order_requests(id):
    session = get_db_session()
    order = session.query(OutageOrder).filter_by(id=id).first()
    if not order:
        raise HTTPException(404, detail="Order does not exist.")
    requests = session.query(ScheduleRequest).filter_by(order_id=order.id, order_type="outage").all()
    for request in requests:
        TopicPublisher(rabbit(), f"schedule.request.{request.order_type}.decline").publish_message(request.id)
    session.commit()


@router.post("/orders/create")
async def create_outage(outage_request: OutageOrderCreationRequest = Depends(lambda request_data=Body(...): validate_request_schema(request_data, OutageOrderCreationRequest))):
    session = get_db_session()
    asset = session.query(Satellite).filter_by(name=outage_request.Target).one_or_none()
    if asset is None:
        asset = session.query(GroundStation).filter_by(name=outage_request.Target).one()
    
    window_start = datetime.fromisoformat(outage_request.Window.Start)
    window_end = datetime.fromisoformat(outage_request.Window.End)
    outage_order = OutageOrder(
        asset_id=asset.id,
        asset_type=asset.asset_type,
        window_start=window_start,
        window_end=window_end,
        duration=window_end-window_start,
    )

    session.add(outage_order)
    session.commit()

    TopicPublisher(rabbit(), f"order.{outage_order.order_type}.created").publish_message(outage_order.id)
    return outage_order.id