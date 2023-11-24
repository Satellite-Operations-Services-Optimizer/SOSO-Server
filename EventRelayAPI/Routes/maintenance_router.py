#from typing import List
from fastapi import APIRouter#, Body, Depends
import logging
from Helpers.activity_helper import get_all_memory_scrubs, get_all_orbit_maneuvers, get_all_orbit_parameter_updates, get_all_payload_diagnostics

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/memory-scrubs")
async def get_memory_scrubs():
    return get_all_memory_scrubs()

@router.get("/orbit-maneuvers")
async def get_orbit_maneuvers():
    return get_all_orbit_maneuvers()

@router.get("/orbit-parameter-updates")
async def get_orbit_parameter_updates():
    return get_all_orbit_parameter_updates()

@router.get("/payload-diagnostic-activites")
async def get_payload_diagnostics():
    return get_all_payload_diagnostics()