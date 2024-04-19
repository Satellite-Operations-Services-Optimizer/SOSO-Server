from fastapi import APIRouter, Body, Depends, Query, HTTPException
import logging
from models.activity_request import ActivityRequest, OutageOrderCreationRequest
from helpers.request_validation_helper import validate_request_schema
from models.activity_request import ActivityRequest
from event_relay_api.helpers.request_validation_helper import validate_request_schema
from app_config import get_db_session, rabbit
from app_config.database.mapping import GroundStationOutageOrder, SatelliteOutageOrder, Satellite, GroundStation, ScheduleRequest
from datetime import timedelta, datetime
from rabbit_wrapper import TopicPublisher
from typing import List
from helpers.queries import create_exposed_schedule_requests_query

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{asset_type}/orders")
async def get_all_outage_orders(asset_type: str, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1), all: bool = Query(False)):
    session = get_db_session()
    OutageOrder = GroundStationOutageOrder if asset_type == "groundstation" else SatelliteOutageOrder
    query = session.query(OutageOrder)
    if not all:
        query = query.limit(per_page).offset((page - 1) * per_page)
    return query.all()

@router.get("/{asset_type}/orders/{id}")
async def get_outage_order(asset_type: str, id: int):
    session = get_db_session()
    OutageOrder = GroundStationOutageOrder if asset_type == "groundstation" else SatelliteOutageOrder
    maintenance_order = session.query(OutageOrder).filter_by(id=id).first()
    if not maintenance_order:
        raise HTTPException(404, detail=f"{asset_type.capitalize()} Outage order with id={id} does not exist.")
    return maintenance_order

@router.get("/{asset_type}/orders/{id}/requests")
async def get_image_order_requests(asset_type: str, id: int, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1), all: bool = Query(False), request_types: List[str] = Query(None)):
    session = get_db_session()
    OutageOrder = GroundStationOutageOrder if asset_type == "groundstation" else SatelliteOutageOrder
    outage_order = session.query(OutageOrder).filter_by(id=id).first()
    if not outage_order:
        raise HTTPException(404, detail=f"{asset_type.capitalize()} Outage order with id={id} does not exist.")
    
    requests_query = create_exposed_schedule_requests_query().filter_by(order_id=id, order_type=outage_order.order_type)
    if request_types:
        requests_query = requests_query.filter(ScheduleRequest.order_type.in_(request_types))
    if not all:
        requests_query = requests_query.limit(per_page).offset((page - 1) * per_page)
    return requests_query.all()

@router.post("/orders/create")
async def create_outage(outage_request: OutageOrderCreationRequest = Depends(lambda request_data=Body(...): validate_request_schema(request_data, OutageOrderCreationRequest))):
    session = get_db_session()
    asset = session.query(Satellite).filter_by(name=outage_request.Target).one()
    OutageOrder = SatelliteOutageOrder
    if asset is None:
        asset = session.query(GroundStation).filter_by(name=outage_request.Target).one()
        OutageOrder = GroundStationOutageOrder
    
    start_time = datetime.fromisoformat(outage_request.Window.Start)
    end_time = datetime.fromisoformat(outage_request.Window.End)
    outage = OutageOrder(
        asset_id=asset.id,
        start_time=start_time,
        end_time=end_time,
        duration=end_time-start_time,
    )
    return outage