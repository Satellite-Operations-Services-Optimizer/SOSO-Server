from typing import List
from fastapi import APIRouter, Body, Depends
import logging
from Models.ScheduleModel import ScheduleModel
from Helpers.schedule_helper import get_all_basic_schedules, get_all_joined_schedules, get_basic_schedule_by_id

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[ScheduleModel])
async def get_basic_schedules(): 
    return get_all_basic_schedules()

@router.get("/id={id}")
async def get_schedule_by_id(id):
    return get_basic_schedule_by_id(id)

@router.get("/complete")
async def get_full_schedule():
    return get_all_joined_schedules()