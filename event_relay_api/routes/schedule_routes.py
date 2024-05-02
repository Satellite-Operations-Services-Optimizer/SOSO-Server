from typing import List
from fastapi import APIRouter, HTTPException, Response
import logging
from app_config import get_db_session, rabbit
from app_config.database.mapping import Schedule, ScheduledEvent, Asset, ScheduleRequest, ContactEvent, GroundStation, ScheduledImaging, ScheduledMaintenance, CaptureOpportunity, SatelliteEclipse, SatelliteOutage, GroundStationOutage, ImageOrder, MaintenanceOrder, OutageOrder
from fastapi.encoders import jsonable_encoder
import os
from fastapi import Query
from sqlalchemy import case
from rabbit_wrapper import TopicPublisher
from helpers.queries import create_exposed_schedule_requests_query
from helpers.utils import paginated_response
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def get_schedules(name: str = Query(None)):
    session = get_db_session()
    if name:
        schedule = session.query(Schedule).filter_by(name=name).first()
        if not schedule:
            raise HTTPException(404, detail="Schedule does not exist.")
        return jsonable_encoder(schedule)
    schedules = session.query(Schedule).all()
    return jsonable_encoder(schedules)

@router.get("/default")
async def get_default_schedule():
    session = get_db_session()
    default_schedule_id = os.getenv('DEFAULT_SCHEDULE_ID')
    schedule = session.query(Schedule).filter_by(id=default_schedule_id).first()
    if not schedule:
        raise HTTPException(404, detail="Default schedule does not exist.")
    return jsonable_encoder(schedule)

@router.post("/{id}/set_reference_time")
async def set_schedule_reference_time(id: int, reference_time: datetime):
    session = get_db_session()
    schedule = session.query(Schedule).filter_by(id=id).first()
    if not schedule:
        raise HTTPException(404, detail="Schedule does not exist.")
    current_time = datetime.now()
    reference_time = reference_time.replace(tzinfo=current_time.tzinfo)
    schedule.time_offset = reference_time - current_time
    session.commit()
    return {"reference_time": reference_time, "time_offset": schedule.time_offset}

@router.get("/requests")
async def get_all_schedule_requests(order_ids: List[int] = Query(None), page: int = Query(1, ge=1), per_page: int = Query(20, ge=1), all: bool = Query(False), order_types: List[str] = Query(None)):
    session = get_db_session()
    requests_subquery = create_exposed_schedule_requests_query()
    if order_ids and len(order_ids) > 0:
        requests_subquery = requests_subquery.filter(ScheduleRequest.order_id.in_(order_ids))
    if order_types:
        requests_subquery = requests_subquery.filter(ScheduleRequest.order_type.in_(order_types))
    total = requests_subquery.count()
    if not all:
        requests_subquery = requests_subquery.limit(per_page).offset((page - 1) * per_page)

    order_types = order_types or []
    if len(order_types) == 0:
        return paginated_response([request._asdict() for request in requests_subquery.all()], total)
    

    requests_subquery = requests_subquery.subquery()
    all_order_tables = {
        "imaging": ImageOrder,
        "maintenance": MaintenanceOrder,
        "outage": OutageOrder,
    }

    requests = []
    for order_type in order_types:
        additional_columns = []
        if order_type=="imaging":
            additional_columns.extend([
                ImageOrder.image_type,
                ImageOrder.latitude,
                ImageOrder.longitude
            ])
        elif order_type=="maintenance":
            additional_columns.append(MaintenanceOrder.description)

        order_table = all_order_tables.get(order_type)
        if order_table:
            requests_query = session.query(
                *requests_subquery.c,
                *additional_columns
            ).join(
                order_table, (order_table.id==requests_subquery.c.order_id) & (order_table.order_type==requests_subquery.c.order_type) & (order_table.order_type==order_type)
            ).order_by(requests_subquery.c.window_start)
            requests.extend([request._asdict() for request in requests_query.all()])
    return paginated_response(requests, total)

@router.post("/requests/{request_id}/decline")
async def decline_schedule_request(request_id: int):
    session = get_db_session()
    request = session.query(ScheduleRequest).filter_by(id=request_id).first()
    if not request:
        raise HTTPException(404, detail="Request does not exist.")
    TopicPublisher(rabbit(), f"schedule.request.{request.order_type}.decline").publish_message(request.id)

@router.get("/{id}/events")
async def scheduled_events_by_id(response: Response, id: int, page: int = Query(1, ge=1), per_page: int = Query(1000, ge=1), all: bool = Query(False), event_types: List[str] = Query(None)):
    session = get_db_session()
    schedule = session.query(Schedule).filter_by(id=id).first()
    if not schedule:
        raise HTTPException(404, detail="Schedule with id={id} does not exist.")

    events_subquery = session.query(
        ScheduledEvent.event_type,
        ScheduledEvent.id,
        Asset.name.label("asset_name"),
        GroundStation.id.label("groundstation_id"),
        GroundStation.name.label("groundstation_name"),
        ScheduleRequest.id.label("request_id"),
        ScheduleRequest.order_id
    ).join(
        Asset, (ScheduledEvent.asset_type==Asset.asset_type) & (ScheduledEvent.asset_id==Asset.id)
    ).outerjoin(
        ScheduleRequest, ScheduledEvent.request_id==ScheduleRequest.id
    ).outerjoin(
        ContactEvent, (ScheduledEvent.event_type==ContactEvent.event_type) & (ScheduledEvent.id==ContactEvent.id)
    ).outerjoin(
        GroundStation, ContactEvent.groundstation_id==GroundStation.id
    ).filter(ScheduledEvent.schedule_id==id).order_by(ScheduledEvent.window_start)
    
    if event_types:
        events_subquery = events_subquery.filter(ScheduledEvent.event_type.in_(event_types))

    total = events_subquery.count()

    if not all:
        events_subquery.limit(per_page).offset((page - 1) * per_page)
    
    events_subquery = events_subquery.subquery()

    all_event_tables = {
        "imaging": ScheduledImaging,
        "maintenance": ScheduledMaintenance,
        "contact": ContactEvent,
        "capture": CaptureOpportunity,
        "eclipse": SatelliteEclipse,
        "sat_outage": SatelliteOutage,
        "gs_outage": GroundStationOutage
    }
    all_order_tables = {
        "imaging": ImageOrder,
        "maintenance": MaintenanceOrder,
        "gs_outage": OutageOrder,
        "sat_outage": OutageOrder
    }
    events = []
    for event_type in event_types:
        if event_type not in all_event_tables:
            continue
        event_table = all_event_tables[event_type]

        additional_columns = []
        if event_type=="imaging":
            additional_columns.extend([
                ImageOrder.image_type,
                ImageOrder.latitude,
                ImageOrder.longitude
            ])
        elif event_type=="capture":
            additional_columns.extend([
                CaptureOpportunity.image_type,
                CaptureOpportunity.latitude,
                CaptureOpportunity.longitude
            ])
        elif event_type=="maintenance":
            additional_columns.append(MaintenanceOrder.description)

        events_query = session.query(
            *event_table.__table__.columns,
            events_subquery.c.asset_name,
            events_subquery.c.groundstation_id,
            events_subquery.c.groundstation_name,
            events_subquery.c.order_id,
            *additional_columns
        ).join(
            event_table, (event_table.id==events_subquery.c.id) & (event_table.event_type==events_subquery.c.event_type) & (event_table.event_type==event_type)
        )

        order_table = all_order_tables.get(event_type)
        if order_table:
            events_query = events_query.join(
                ScheduleRequest,
                ScheduleRequest.id==events_subquery.c.request_id
            ).join(
                order_table, order_table.id==ScheduleRequest.order_id
            )

        events.extend(events_query.order_by(event_table.window_start).all())

    return paginated_response([event._asdict() for event in events], total)