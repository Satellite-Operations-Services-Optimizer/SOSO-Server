from fastapi import APIRouter, Body, Depends
import logging
from models.activity_request import ActivityRequest
from helpers.request_validation_helper import validate_request_schema
from models.activity_request import ActivityRequest
from event_relay_api.helpers.request_validation_helper import validate_request_schema
from app_config import rabbit, ServiceQueues

from rabbit_wrapper import Publisher

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/maintenance-activity-requests")
async def handle_request(maintenance_request: ActivityRequest = Depends(lambda request_data=Body(...): validate_request_schema(request_data, ActivityRequest))):
    publisher = Publisher(rabbit(), ServiceQueues.SAT_ACTIVITIES)
    publisher.publish_message(maintenance_request)