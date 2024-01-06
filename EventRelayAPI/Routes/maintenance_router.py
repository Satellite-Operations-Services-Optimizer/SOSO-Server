from fastapi import APIRouter, Body, Depends
import logging
from Helpers.activity_helper import get_all_memory_scrubs, get_all_orbit_maneuvers, get_all_orbit_parameter_updates, get_all_payload_diagnostics
from Models.ActivityRequestModel import ActivityRequest
from Helpers.request_validation_helper import validate_request_schema
from config import rabbit, ServiceQueues
from rabbit_wrapper import Publisher

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

@router.post("/maintenance-activity-requests")
async def handle_request(maintenance_request: ActivityRequest = Depends(lambda request_data=Body(...): validate_request_schema(request_data, ActivityRequest))):
    publisher = Publisher(rabbit(), ServiceQueues.SAT_ACTIVITIES)
    publisher.publish_message(maintenance_request)