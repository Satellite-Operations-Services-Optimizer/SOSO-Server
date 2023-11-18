from sqlalchemy.orm import Session
from pydantic import BaseModel
from pydantic import ValidationError
from Models import RequestModel
from datetime import timedelta, datetime
from Models.RequestModel import ActivityRequest

from config.database import Base

outage_order = Base.classes.outage_order
maintenance_order = Base.classes.maintenance_order
image_order = Base.classes.image_order
schedule = Base.classes.schedule
scheduled_images = Base.classes.scheduled_images
scheduled_maintenance = Base.classes.scheduled_maintenance
scheduled_outages = Base.classes.scheduled_outages
satellite = Base.classes.satellite
ground_station = Base.classes.ground_station
ground_station_request = Base.classes.ground_station_request
        
def get_maintenence_request(db: Session, maintenence_id: int):
    
    return db.query(maintenance_order).filter(maintenance_order.id == maintenence_id).first()

def create_maintenence_request(db: Session, request: ActivityRequest) -> maintenance_order:
    db_request = maintenance_order(
        asset_name = request.Target,
        description=request.Activity,
        start_time=datetime.fromisoformat(request.Window.Start),
        end_time=datetime.fromisoformat(request.Window.End),
        duration=timedelta(seconds = int(request.Duration)),
        repetition=int(request.RepeatCycle.Repetition),
        frequency_min=int(request.RepeatCycle.Frequency.MinimumGap),
        frequency_max=int(request.RepeatCycle.Frequency.MaximumGap),        
        operations_flag=request.PayloadOutage
    )
    #db = SessionLocal() 
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    db.close()
    
    return db_request


def create_outage_request(db: Session, request: RequestModel.OutageRequest) -> outage_order:
    
    db_request = outage_order(
        asset_name = request.Target,
        description=request.Activity,
        start_time=datetime.fromisoformat(request.Window.Start),
        end_time=datetime.fromisoformat(request.Window.End),
    )
    #db = SessionLocal() 
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    db.close()
    
    return db_request

def get_outage_request(db: Session, outage_id: int):
    
    return db.query(outage_order).filter(outage_order.id == outage_id).first()

def get_image_request(db: Session, image_id: int):
    
    return db.query(image_order).filter(image_order.id == image_id).first()

#individual activities

def get_scheduled_maintenence(db: Session, id: int):
    return db.query(scheduled_maintenance).filter(scheduled_maintenance.manintenace_id == id)

def get_scheduled_outage(db: Session, id: int):
    return db.query(scheduled_outages).filter(scheduled_outages.outage_id == id).first()

def get_scheduled_image(db: Session, id: int):
    return db.query(scheduled_images).filter(scheduled_images.image_id == id)  

# statellite schedule
def get_schedule(db: Session, id: int):
    return db.query(schedule).filter(schedule.id == id) 

# groud station schedule
def get_ground_station_request(db: Session, id: int):
    return db.query(ground_station_request).filter(ground_station_request.id == id) 

# all activities of an order request
def get_all_repeats_from_maintenance_request(db: Session, id: int):
    return db.queryquery(scheduled_maintenance).filter_by(maintenance_id=id).all()

def get_all_repeats_from_image_request(db: Session, id: int):
    return db.queryquery(scheduled_images).filter_by(image_id=id).all()
 
