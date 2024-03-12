import warnings
import logging
# Suppress all warnings, including SQLAlchemy warnings
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.CRITICAL + 1)

from app_config import get_db_session
from app_config.database.mapping import ScheduleRequest, Schedule, Satellite, CaptureOpportunity, ImageOrder, SatelliteOutage, SystemOrder, ScheduledEvent, TransmittedEvent, GroundStation, ContactEvent
from pathlib import Path
from sqlalchemy import func


def create_report():
    session = get_db_session()
    total_order_count = session.query(SystemOrder).count()
    total_request_count = session.query(ScheduleRequest).count()
    print("===========Overall stats===========")
    print(f"Total order count: {total_order_count}")
    request_count_by_type = session.query(
        ScheduleRequest.order_type,
        func.count(ScheduleRequest.id)
    ).group_by(ScheduleRequest.order_type).all()

    print(f"Total request count: {total_request_count}")
    print_request_breakdown(session.query(ScheduleRequest).subquery(), "   ")


    print("\n======Breakdown by order type======")

    for order_type, request_count in request_count_by_type:
        order_count = session.query(SystemOrder).filter_by(order_type=order_type).count()
        print(f"Total {order_type.capitalize()} order count: {order_count}")
        print(f"Total {order_type.capitalize()} request count: {request_count}")
        requests_subquery = session.query(ScheduleRequest).filter_by(order_type=order_type).subquery()
        print_request_breakdown(requests_subquery, "   ")
    
    print("\n==========Scheduled Events=========")
    print("------------Per satellite-----------")
    for satellite_id, satellite_name in session.query(Satellite.id, Satellite.name).all():
        total_event_count = session.query(TransmittedEvent).filter_by(asset_id=satellite_id).count()
        print(f"{satellite_name}: {total_event_count} events scheduled")

        event_count_by_type = session.query(
            TransmittedEvent.event_type,
            func.count(TransmittedEvent.id)
        ).filter_by(
            asset_id=satellite_id
        ).group_by(TransmittedEvent.event_type).all()
        for event_type, request_count in event_count_by_type:
            print(f"   {event_type} events: {request_count}")

    
    print("\n----------Per groundstation---------")
    for gs_id, gs_name in session.query(GroundStation.id, GroundStation.name).all():
        total_contacts = session.query(ContactEvent).filter(
            ContactEvent.groundstation_id==gs_id,
            ContactEvent.total_transmission_time > 0
        ).count()
        print(f"{gs_name}: {total_contacts} scheduled contacts")


def print_request_breakdown(requests_subquery, indent):
    session = get_db_session()
    request_count_by_status = session.query(
        requests_subquery.c.status,
        func.count(requests_subquery.c.id)
    ).group_by(requests_subquery.c.status).all()
    for request_status, count in request_count_by_status:
        print(f"{indent}{request_status.capitalize()} requests: {count}")
        breakdown_by_reason = session.query(
            requests_subquery.c.status_message,
            func.count(requests_subquery.c.id)
        ).filter_by(status=request_status).group_by(
            requests_subquery.c.status,
            requests_subquery.c.status_message
        ).all()
        if len(breakdown_by_reason) > 0 and request_status != "received" and request_status != "scheduled" and request_status != "processing":
            for reason, count in breakdown_by_reason:
                print(f"{indent}  {count}: Reason: {reason or "Unspecified"}")
    



if __name__ == "__main__":
    create_report()