from typing import List
from fastapi import APIRouter, Body, Depends, HTTPException
import logging
from models.ScheduleModel import ScheduleModel
from Helpers.schedule_utils import get_all_basic_schedules, get_all_joined_schedules, get_basic_schedule_by_id
from app_config import get_db_session
from app_config.database.mapping import Schedule, ScheduledEvent
from fastapi.encoders import jsonable_encoder

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/basic")
async def get_basic_schedules(): 
    return get_all_basic_schedules()

@router.get("/{id}")
async def get_schedule_by_id(id):
    return get_basic_schedule_by_id(id)

@router.get("/complete")
async def get_full_schedule():
    return get_all_joined_schedules()

@router.get("/")
async def get_schedules():
    session = get_db_session()
    schedules = session.query(Schedule).all()
    return jsonable_encoder(schedules)

@router.get("/{id}/events")
async def scheduled_events_by_id(id: int):
    session = get_db_session()
    schedule = session.query(Schedule).filter_by(id=id).first()
    if not schedule:
        raise HTTPException(404, detail="Schedule does not exist.")

    events = session.query(ScheduledEvent).filter_by(schedule_id=id).all()
    return jsonable_encoder(events)


@router.get("/name={name}/events/{type}")
async def scheduled_events_by_name(name: str):
    session = get_db_session()
    schedule = session.query(Schedule).filter_by(name=name).first()
    if not schedule:
        raise HTTPException(404, detail="Schedule does not exist.")
    return scheduled_events_by_id(schedule.id)