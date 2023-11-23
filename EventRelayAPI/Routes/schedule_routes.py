from fastapi import APIRouter, Body, Depends
import logging
from Helpers.schedule_utils import get_all_schedules

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def get_schedules(): 
    return get_all_schedules()