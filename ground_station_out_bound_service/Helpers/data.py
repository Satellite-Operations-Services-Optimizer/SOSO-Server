from datetime import datetime
from app_config.database.mapping import Base,Schedule, ImageOrder, MaintenanceOrder, OutageOrder, OutboundSchedule, ScheduledImaging, ScheduledMaintenance, ScheduledContact, GroundStationRequest, GroundStation, Satellite, ScheduleRequest, ScheduledOutage
from app_config.database.setup import  scoped_session
from models.QueueModel import QueueRequest, QueueDetails
from models.ScheduleModel import maintenance_activity, image_activity, downlink_activity, outbound_schedule


def get_schedule(schedule_id: int ):
    db = scoped_session
    return db.query(Schedule).filter(Schedule.schedule.id == schedule_id).first();

def get_ground_station_request(request_id: int ):
    db = scoped_session
    return db.query(GroundStationRequest).filter(GroundStationRequest.id == request_id).first();

def get_maintenance_order(maintenance_id: int):
    db = scoped_session
    return db.query(MaintenanceOrder).filter(MaintenanceOrder.id == maintenance_id).first()

def get_outage_request(outage_id: int):
    db = scoped_session
    return db.query(OutageOrder).filter(OutageOrder.id == outage_id).first()

def get_image_order(image_id: int):
    db = scoped_session
    return db.query(ImageOrder).filter(ImageOrder.id == image_id).first()

def get_scheduled_image(image_id: int,):
    db = scoped_session
    return db.query(ScheduledImaging).filter(ScheduledImaging.request_id == image_id).first()

def get_scheduled_maintenance(maintenance_id: int):
    db = scoped_session
    return db.query(ScheduledMaintenance).filter(ScheduledMaintenance.request_id == maintenance_id).first()

def get_scheduled_outage(outage_id: int):
    db = scoped_session
    return db.query(ScheduledOutage).filter(ScheduledOutage.request_id == outage_id).first()

def get_scheduled_contact(contact_id: int):
    db = scoped_session
    return db.query(ScheduledContact).filter(ScheduledContact.id == contact_id).first()

def get_all_scheduled_images_from_schedule(schedule_id: int):
    db = scoped_session
    return db.query(ScheduledImaging).filter(ScheduledImaging.id == schedule_id).all()

def get_all_scheduled_maintenence_from_schedule(schedule_id: int):
    db = scoped_session
    return db.query(ScheduledMaintenance).filter(ScheduledMaintenance.id == schedule_id).all()

def get_all_scheduled_outage_from_schedule(schedule_id: int):
    db = scoped_session
    return db.query(ScheduledOutage).filter(ScheduledOutage.id == schedule_id).all()

def get_satellite(satellite_id: int):
    db = scoped_session
    return db.query(Satellite).filter(Satellite.id == satellite_id).first()

def get_ground_station_request(request_id: int):
    db = scoped_session
    return db.query(GroundStationRequest).filter(GroundStationRequest.id == request_id).first()

def get_ground_station(gs_id: int):
    db = scoped_session
    return db.query(GroundStation).filter(GroundStation.id == gs_id).first()

def get_schedule_request(request_id: int, status: str):
    db = scoped_session
    return db.query(ScheduleRequest).filter(ScheduleRequest.order_id == request_id, ScheduleRequest.status == status).first()

def get_all_scheduled_images_from_contact(contact_id: int):
    db = scoped_session
    return db.query(ScheduledImaging).filter(ScheduledImaging.downlink_contact_id == contact_id).all()

def get_outbound_schedule(contact_id):
    db = scoped_session
    return db.query(OutboundSchedule).filter(OutboundSchedule.contact_id == contact_id).first()

def create_outbound_schedule(contact_id: int , satellite_name: str, active_window: list[datetime, datetime], image: list[image_activity] = None, maintenance: list[maintenance_activity] = None, downlink: list[downlink_activity] = None):
    db = scoped_session
    schedule = outbound_schedule(contact_id = contact_id,
                                 satellite_name = satellite_name,
                                 active_window = active_window,
                                 image_activities = image,
                                 maintenance_activities = maintenance,
                                 downlink_activities = downlink,
                                 schedule_status = "created")
    db.add(schedule)
    db.commit()
    return get_outbound_schedule(contact_id)

def update_outbound_schedule(outbound_schedule: OutboundSchedule):
    db = scoped_session
       
    schedule = db.query(OutboundSchedule).filter_by(contact_id = outbound_schedule.contact_id).with_for_update().one()
    schedule.contact_id = outbound_schedule.contact_id
    schedule.satellite_name = outbound_schedule.satellite_name
    schedule.active_window = outbound_schedule.active_window
    schedule.image_activities = outbound_schedule.image
    schedule.maintenance_activities = outbound_schedule.maintenance
    schedule.downlink_activities = outbound_schedule.downlink
    schedule.schedule_status = "updated"
    
    db.add(schedule)
    db.commit()
    return get_outbound_schedule(schedule.contact_id)

def update_contact_with_downlink(scheduled_contact: ScheduledContact):
    db = scoped_session
       
    contact = db.query(ScheduledContact).filter_by(id = scheduled_contact.id).with_for_update().one()
    
    contact.downlink_images = scheduled_contact.downlink_images
    
    db.add(contact)
    db.commit()
    return get_outbound_schedule(contact.id)
    