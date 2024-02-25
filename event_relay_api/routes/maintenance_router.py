from fastapi import APIRouter, Body, Depends
import logging
from models.activity_request import ActivityRequest
from helpers.request_validation_helper import validate_request_schema
from models.activity_request import ActivityRequest
from event_relay_api.helpers.request_validation_helper import validate_request_schema
from app_config import get_db_session
from app_config.database.mapping import MaintenanceOrder, Satellite
from fastapi import Query   

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/orders/new")
async def create_maintenance_request(maintenance_request: ActivityRequest = Depends(lambda request_data=Body(...): validate_request_schema(request_data, ActivityRequest))):
    session = get_db_session()
    
    satellite = session.query(Satellite).filter_by(name=maintenance_request["Target"])
    maintenance = MaintenanceOrder(
        description = maintenance_request["Activity"],
        end_time = maintenance_request["Window"]["End"],
        start_time = maintenance_request["Window"]["Start"],
        duration = maintenance_request["Duration"],
        revisit_frequency = maintenance_request["RepeatCycle"]["Frequency"],
        visits_remaining = maintenance_request["RepeatCycle"]["Repetition"],
        operations_flag = maintenance_request["PayloadOutage"],
        asset_id = satellite.id,
        asset_type = "satellite"
    )
    session.add(maintenance)
    session.commit()

@router.get("/orders")
async def get_all_maintenance_orders(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1), all: bool = Query(False)):
    session = get_db_session()
    query = session.query(MaintenanceOrder)
    if not all:
        query.limit(per_page).offset((page - 1) * per_page)
    return query.all()