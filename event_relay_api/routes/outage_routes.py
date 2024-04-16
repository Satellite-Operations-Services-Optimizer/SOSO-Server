from fastapi import APIRouter, Body, Depends, Query, HTTPException
import logging
from models.activity_request import ActivityRequest, OutageOrderCreationRequest
from helpers.request_validation_helper import validate_request_schema
from models.activity_request import ActivityRequest
from event_relay_api.helpers.request_validation_helper import validate_request_schema
from app_config import get_db_session, rabbit
from app_config.database.mapping import GroundStationOutageOrder, SatelliteOutageOrder, Satellite, GroundStation
from datetime import timedelta, datetime
from rabbit_wrapper import TopicPublisher

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/orders/{asset_type}")
async def get_all_outage_orders(asset_type: str, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1), all: bool = Query(False)):
    session = get_db_session()
    OutageOrder = GroundStationOutageOrder if asset_type == "groundstation" else SatelliteOutageOrder
    query = session.query(OutageOrder)
    if not all:
        query.limit(per_page).offset((page - 1) * per_page)
    return query.all()

@router.get("/orders/{asset_type}/{id}")
async def get_outage_order(asset_type: str, id: int):
    session = get_db_session()
    OutageOrder = GroundStationOutageOrder if asset_type == "groundstation" else SatelliteOutageOrder
    maintenance_order = session.query(OutageOrder).filter_by(id=id).first()
    if not maintenance_order:
        raise HTTPException(404, detail=f"{asset_type.capitalize()} Outage order with id={id} does not exist.")
    return maintenance_order

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