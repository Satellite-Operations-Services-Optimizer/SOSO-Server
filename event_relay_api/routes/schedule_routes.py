from typing import List
from fastapi import APIRouter, HTTPException
import logging
from app_config import get_db_session
from app_config.database.mapping import Schedule, ScheduledEvent, Asset, ScheduleRequest
from fastapi.encoders import jsonable_encoder
from fastapi import Query

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

    query = session.query(
        ScheduledEvent.event_type,
        ScheduledEvent.id,
        ScheduledEvent.start_time,
        ScheduledEvent.duration,
        ScheduledEvent.asset_type,
        ScheduledEvent.asset_id,
        Asset.name.label("asset_name"),
        ScheduleRequest.order_id
    ).join(
        Asset, (ScheduledEvent.asset_type==Asset.asset_type) & (ScheduledEvent.asset_id==Asset.id)
    ).join(
        ScheduleRequest, ScheduledEvent.request_id==ScheduleRequest.id, isouter=True
    ).filter(ScheduledEvent.schedule_id==id).order_by(ScheduledEvent.start_time)
    
    if event_types:
        query = query.filter(ScheduledEvent.event_type.in_(event_types))

    if not all:
        query.limit(per_page).offset((page - 1) * per_page).all()

    return [event._asdict() for event in query.all()]

def scheduled_event_columns():
    return []

@router.get("/name={name}")
async def scheduled_events_by_name(name: str):
    session = get_db_session()
    schedule = session.query(Schedule).filter_by(name=name).first()
    if not schedule:
        raise HTTPException(404, detail="Schedule does not exist.")
    return jsonable_encoder(schedule)