from fastapi import APIRouter, Body, Depends, Query, HTTPException
import logging
from models.activity_request import ActivityRequest
from helpers.request_validation_helper import validate_request_schema
from models.activity_request import ActivityRequest
from event_relay_api.helpers.request_validation_helper import validate_request_schema
from app_config import get_db_session, rabbit
from app_config.database.mapping import MaintenanceOrder, Satellite, ScheduleRequest
from datetime import timedelta, datetime
from rabbit_wrapper import TopicPublisher
from typing import List
from helpers.queries import create_exposed_schedule_requests_query

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/orders")
async def get_all_maintenance_orders(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1), all: bool = Query(False)):
    session = get_db_session()
    query = session.query(MaintenanceOrder)
    if not all:
        query = query.limit(per_page).offset((page - 1) * per_page)
    return query.all()

@router.get("/orders/{id}")
async def get_maintenance_order(id):
    session = get_db_session()
    maintenance_order = session.query(MaintenanceOrder).filter_by(id=id).first()
    if not maintenance_order:
        raise HTTPException(404, detail="Maintenance order with id={id} does not exist.")
    return maintenance_order

@router.get("orders/{id}/requests")
async def get_maintenance_order_requests(id: int, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1), all: bool = Query(False), request_types: List[str] = Query(None)):
    session = get_db_session()
    maintenance_order = session.query(MaintenanceOrder).filter_by(id=id).first()
    if not maintenance_order:
        raise HTTPException(404, detail="Maintenance order with id={id} does not exist.")
    
    requests_query = create_exposed_schedule_requests_query().filter_by(order_id=id, order_type=maintenance_order.order_type)
    if request_types:
        requests_query = requests_query.filter(ScheduleRequest.order_type.in_(request_types))
    if not all:
        requests_query = requests_query.limit(per_page).offset((page - 1) * per_page)
    return requests_query.all()

@router.post("/orders/create")
async def create_maintenance_request(maintenance_request: ActivityRequest = Depends(lambda request_data=Body(...): validate_request_schema(request_data, ActivityRequest))):
    session = get_db_session()
    satellite = session.query(Satellite).filter_by(name=maintenance_request["Target"]).one()

    duration = timedelta(seconds=int(maintenance_request.Duration))

    if maintenance_request.RepeatCycle.Repetition == "Null":
        number_of_visits = 1
        revisit_frequency = timedelta(seconds=0)
        revisit_frequency_max = timedelta(seconds=0)
    else:
        number_of_visits = int(maintenance_request.RepeatCycle.Repetition) + 1
        revisit_frequency = timedelta(seconds=int(maintenance_request.RepeatCycle.Frequency.MinimumGap))
        revisit_frequency_max = timedelta(seconds=int(maintenance_request.RepeatCycle.Frequency.MaximumGap))
    payload_outage = maintenance_request.PayloadOutage.lower()=="true"
    maintenance_order = MaintenanceOrder(
        asset_id=int(satellite.id),
        description=maintenance_request.Activity,
        start_time=datetime.fromisoformat(maintenance_request.Window.Start),
        end_time=datetime.fromisoformat(maintenance_request.Window.End),
        duration=duration,
        number_of_visits=number_of_visits,
        revisit_frequency=revisit_frequency,
        revisit_frequency_max=revisit_frequency_max,
        payload_outage=payload_outage,
    )
    
    session.add(maintenance_order)
    session.commit()

    TopicPublisher(rabbit(), f"order.{maintenance_order.order_type}.created").publish_message(maintenance_order.id)
    return maintenance_order.id
