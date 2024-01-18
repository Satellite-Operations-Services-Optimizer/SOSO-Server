from config.database import Base, db_engine, scoped_session, db_session
from Models.QueueModel import QueueRequest, QueueDetails

schedule = Base.classes.schedule
ground_station_request = Base.classes.ground_station_request
scheduled_images = Base.classes.scheduled_images
scheduled_maintenance = Base.classes.scheduled_maintenance
scheduled_outages = Base.classes.scheduled_outages
satellite = Base.classes.satellite
image_order = Base.classes.image_order
maintenance_order = Base.classes.maintenance_order
outage_order = Base.classes.outage_order
ground_station = Base.classes.ground_station
schedule_request = Base.classes.schedule_request
scheduled_contact = Base.classes.scheduled_contact

def get_schedule(schedule_id: int ):
    db = db_session
    return db.query(schedule).filter(schedule.id == schedule_id).first();

def get_ground_station_request(request_id: int ):
    db = db_session
    return db.query(ground_station_request).filter(ground_station_request.id == request_id).first();

def get_maintenance_order(maintenance_id: int):
    db = db_session
    return db.query(maintenance_order).filter(maintenance_order.id == maintenance_id).first()

def get_outage_request(outage_id: int):
    db = db_session
    return db.query(outage_order).filter(outage_order.id == outage_id).first()

def get_image_order(image_id: int):
    db = db_session
    return db.query(image_order).filter(image_order.id == image_id).first()

def get_scheduled_image(image_id: int,):
    db = db_session
    return db.query(scheduled_images).filter(scheduled_images.request_id == image_id).first()

def get_scheduled_maintenance(maintenance_id: int):
    db = db_session
    return db.query(scheduled_maintenance).filter(scheduled_maintenance.request_id == maintenance_id).first()

def get_scheduled_outage(outage_id: int):
    db = db_session
    return db.query(scheduled_outages).filter(scheduled_outages.request_id == outage_id).first()

def get_scheduled_contact(contact_id: int):
    db = db_session
    return db.query(scheduled_contact).filter(scheduled_contact.id == contact_id).first()

def get_all_scheduled_images_from_schedule(schedule_id: int):
    db = db_session
    return db.query(scheduled_images).filter(scheduled_images.id == schedule_id).all()

def get_all_scheduled_maintenence_from_schedule(schedule_id: int):
    db = db_session
    return db.query(scheduled_maintenance).filter(scheduled_maintenance.id == schedule_id).all()

def get_all_scheduled_outage_from_schedule(schedule_id: int):
    db = db_session
    return db.query(scheduled_outages).filter(scheduled_outages.id == schedule_id).all()

def get_satellite(satellite_id: int):
    db = db_session
    return db.query(satellite).filter(satellite.id == satellite_id).first()

def get_ground_station_request(request_id: int):
    db = db_session
    return db.query(ground_station_request).filter(ground_station_request.id == request_id).first()

def get_ground_station(gs_id: int):
    db = db_session
    return db.query(ground_station).filter(ground_station.id == gs_id).first()

def get_schedule_request(request_id: int, status: str):
    db = db_session
    return db.query(schedule_request).filter(schedule_request.order_id == request_id, schedule_request.status == status).first()

def get_all_scheduled_images_from_contact(contact_id: int):
    db = db_session
    return db.query(scheduled_images).filter(scheduled_images.downlink_contact_id == contact_id).all()
