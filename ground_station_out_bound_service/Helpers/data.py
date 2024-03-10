from datetime import datetime
from app_config.database.mapping import Schedule, ImageOrder, MaintenanceOrder, OutageOrder, OutboundSchedule, ScheduledImaging, ScheduledMaintenance, ContactEvent, GroundStationRequest, GroundStation, Satellite, ScheduleRequest, ScheduledOutage
from app_config import get_db_session
from ground_station_out_bound_service.models.ScheduleModel import outbound_schedule
from fastapi.encoders import jsonable_encoder

db = get_db_session()
def get_schedule(schedule_id: int ):
    
    return db.query(Schedule).filter(Schedule.schedule.id == schedule_id).first();

def get_ground_station_request(request_id: int ):
    
    return db.query(GroundStationRequest).filter(GroundStationRequest.id == request_id).first();

def get_maintenance_order(maintenance_id: int):
    
    return db.query(MaintenanceOrder).filter(MaintenanceOrder.id == maintenance_id).first()

def get_outage_request(outage_id: int):
    
    return db.query(OutageOrder).filter(OutageOrder.id == outage_id).first()

def get_image_order(image_id: int):
    
    return db.query(ImageOrder).filter(ImageOrder.id == image_id).first()

def get_scheduled_image(image_id: int,):
    
    return db.query(ScheduledImaging).filter(ScheduledImaging.request_id == image_id).first()

def get_scheduled_maintenance(maintenance_id: int):
    
    return db.query(ScheduledMaintenance).filter(ScheduledMaintenance.request_id == maintenance_id).first()

def get_scheduled_outage(outage_id: int):
    
    return db.query(ScheduledOutage).filter(ScheduledOutage.request_id == outage_id).first()

def get_scheduled_contact(contact_id: int):
    
    return db.query(ContactEvent).filter(ContactEvent.id == contact_id).first()

def get_all_scheduled_images_from_schedule(schedule_id: int):
    
    return db.query(ScheduledImaging).filter(ScheduledImaging.id == schedule_id).all()

def get_all_scheduled_maintenence_from_schedule(schedule_id: int):
    
    return db.query(ScheduledMaintenance).filter(ScheduledMaintenance.id == schedule_id).all()

def get_all_scheduled_outage_from_schedule(schedule_id: int):
    
    return db.query(ScheduledOutage).filter(ScheduledOutage.id == schedule_id).all()

def get_satellite(satellite_id: int):
    
    return db.query(Satellite).filter(Satellite.id == satellite_id).first()

def get_ground_station_request(request_id: int):
    
    return db.query(GroundStationRequest).filter(GroundStationRequest.id == request_id).first()

def get_ground_station(gs_id: int):
    
    return db.query(GroundStation).filter(GroundStation.id == gs_id).first()

def get_schedule_request(request_id: int, status: str):
    
    return db.query(ScheduleRequest).filter(ScheduleRequest.id == request_id, ScheduleRequest.status == status).first()

def get_all_scheduled_images_from_contact(contact_id: int):
    
    return db.query(ScheduledImaging).filter(ScheduledImaging.downlink_contact_id == contact_id).all()

def get_outbound_schedule(contact_id):
    
    return db.query(OutboundSchedule).filter(OutboundSchedule.contact_id == contact_id).first()

def create_outbound_schedule_with_image(contact_id, satellite_name, active_window, image):
    
    schedule = OutboundSchedule(contact_id = contact_id,
                                 satellite_name = satellite_name,
                                 activity_window = active_window,
                                 image_activities = [jsonable_encoder(image)],                                 
                                 schedule_status = "created")
    db.add(schedule)
    db.commit()
    return get_outbound_schedule(contact_id)

def create_outbound_schedule_with_maintenance(contact_id, satellite_name, active_window, maintenance ):
    
    schedule = OutboundSchedule(contact_id = contact_id,
                                 satellite_name = satellite_name,
                                 activity_window = active_window,
                                 maintenance_activities = [jsonable_encoder(maintenance)],
                                 schedule_status = "created")
    db.add(schedule)
    db.commit()
    return get_outbound_schedule(contact_id)

def create_outbound_schedule_with_downlink(contact_id, satellite_name, active_window, downlink ):
    
    schedule = OutboundSchedule(contact_id = contact_id,
                                 satellite_name = satellite_name,
                                 activity_window = active_window,
                                 downlink_activities = [jsonable_encoder(downlink)],
                                 schedule_status = "created")
    db.add(schedule)
    db.commit()
    return get_outbound_schedule(contact_id)

def update_outbound_schedule(outbound_schedule: outbound_schedule):
    
       
    schedule = db.query(OutboundSchedule).filter_by(contact_id = outbound_schedule.contact_id).with_for_update().one()
    schedule.contact_id = outbound_schedule.contact_id
    schedule.satellite_name = outbound_schedule.satellite_name
    schedule.activity_window = outbound_schedule.activity_window
    schedule.image_activities = outbound_schedule.image_activities
    schedule.maintenance_activities = outbound_schedule.maintenance_activities
    schedule.downlink_activities = outbound_schedule.downlink_activities
    schedule.schedule_status = "updated"
   
    db.commit()
    return get_outbound_schedule(schedule.contact_id)

def update_contact_with_downlink(scheduled_contact: ContactEvent):
    
       
    contact = db.query(ContactEvent).filter_by(id = scheduled_contact.id).with_for_update().one()
    
    contact.downlink_images = scheduled_contact.downlink_images
    
    db.commit()
    return get_outbound_schedule(contact.id)

def update_schedule_request_status(request_ids: list[int], status: str):
    
    
    schedule_requests = db.query(ScheduleRequest).filter(ScheduleRequest.id.in_(request_ids)).with_for_update().all()
    for request in schedule_requests:
        request.schedule_request_status = status
    
    db.commit()
    
    pass   
        
    