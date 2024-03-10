from typing import List
from fastapi import APIRouter, HTTPException
import logging
from app_config import get_db_session
from app_config.database.mapping import Schedule, ScheduledEvent, Asset, ScheduleRequest, ContactEvent, GroundStation, ScheduledImaging, ScheduledMaintenance, CaptureOpportunity, SatelliteEclipse, SatelliteOutage, GroundStationOutage, ImageOrder, MaintenanceOrder, GroundStationOutageOrder, SatelliteOutageOrder
from fastapi.encoders import jsonable_encoder
from fastapi import Query
from sqlalchemy import case

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def get_schedules():
    session = get_db_session()
    schedules = session.query(Schedule).all()
    return jsonable_encoder(schedules)

@router.get("/{id}/events")
async def scheduled_events_by_id(id: int, page: int = Query(1, ge=1), per_page: int = Query(1000, ge=1), all: bool = Query(False), event_types: List[str] = Query(None)):
    session = get_db_session()
    schedule = session.query(Schedule).filter_by(id=id).first()
    if not schedule:
        raise HTTPException(404, detail="Schedule does not exist.")

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
    ).filter(ScheduledEvent.schedule_id==id).order_by(ScheduledEvent.start_time)
    
    if event_types:
        events_subquery = events_subquery.filter(ScheduledEvent.event_type.in_(event_types))

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
        "gs_outage": GroundStationOutageOrder,
        "sat_outage": SatelliteOutageOrder,
    }
    events = []
    for event_type in event_types:
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
            events_subquery, (event_table.id==events_subquery.c.id) & (event_table.event_type==events_subquery.c.event_type)
        )

        order_table = all_order_tables.get(event_type)
        if order_table:
            events_query = events_query.join(
                ScheduleRequest,
                ScheduleRequest.id==events_subquery.c.request_id
            ).join(
                order_table, order_table.id==ScheduleRequest.order_id
            )

        events.extend(events_query.order_by(event_table.start_time).all())

    return [event._asdict() for event in events]

@router.get("/name={name}")
async def scheduled_events_by_name(name: str):
    session = get_db_session()
    schedule = session.query(Schedule).filter_by(name=name).first()
    if not schedule:
        raise HTTPException(404, detail="Schedule does not exist.")
    return jsonable_encoder(schedule)