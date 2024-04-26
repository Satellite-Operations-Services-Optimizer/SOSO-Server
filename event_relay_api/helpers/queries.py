from app_config import get_db_session
from app_config.database.mapping import ScheduleRequest, Asset

def create_exposed_schedule_requests_query():
    session = get_db_session()
    query = session.query(
        ScheduleRequest.id,
        ScheduleRequest.order_id,
        ScheduleRequest.order_type,
        ScheduleRequest.window_start,
        ScheduleRequest.window_end,
        ScheduleRequest.duration,
        ScheduleRequest.delivery_deadline,
        ScheduleRequest.uplink_size,
        ScheduleRequest.downlink_size,
        ScheduleRequest.power_usage,
        ScheduleRequest.priority,
        ScheduleRequest.status,
        ScheduleRequest.status_message,
        ScheduleRequest.asset_id,
        ScheduleRequest.asset_type,
        Asset.name.label('asset_name')
    ).join(
        Asset,
        (Asset.id==ScheduleRequest.asset_id) & (Asset.asset_type==ScheduleRequest.asset_type),
        isouter=True
    ).order_by(ScheduleRequest.window_start)



    return query