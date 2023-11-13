from sqlalchemy.orm import Session
from pydantic import BaseModel
from pydantic import ValidationError
from Models import RequestModel
from Database.database import SessionLocal, engine
from Database import db_schemas, db_model
from datetime import timedelta, datetime
from Models.RequestModel import ActivityRequest

from config.database import maintenence_order, image_order, outage_order, schedule, scheduled_maintenance, scheduled_images, scheduled_outages, ground_station_request

        
def get_maintenence_request(db: Session, maintenence_id: int):
    
    return db.query(maintenence_order).filter(maintenence_order.id == maintenence_id).first()

def create_maintenence_request(db: Session, request: ActivityRequest) -> maintenence_order:
    db_request = maintenence_order(
        asset_name = request.Target,
        description=request.Activity,
        start_time=datetime.fromisoformat(request.Window.Start),
        end_time=datetime.fromisoformat(request.Window.End),
        duration=timedelta(seconds=int(request.Duration)),
        repetition=timedelta(seconds=int(request.RepeatCycle.Repetition)),
        frequency_min=timedelta(seconds=int(request.RepeatCycle.Frequency.MinimumGap)),
        frequency_max=timedelta(seconds=int(request.RepeatCycle.Frequency.MaximumGap)),        
        operations_flag=request.PayloadOutage
    )
    db = SessionLocal() 
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    db.close()
    
    return db_request


def create_outage_request(db: Session, request: RequestModel.OutageRequest):
    
    db_request = outage_order(
        asset_name = request.Target,
        description=request.Activity,
        start_time=datetime.fromisoformat(request.Window.Start),
        end_time=datetime.fromisoformat(request.Window.End),
    )
    db = SessionLocal() 
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    db.close()
    
    return db_request

def get_outage_request(db: Session, outage_id: int):
    
    return db.query(outage_order).filter(outage_order.id == outage_id).first()

def get_scheduled_maintenence(db: Session, id: int):
    return db.query(scheduled_maintenance).filter(scheduled_maintenance.manintenace_id == id)

def get_scheduled_outage(db: Session, id: int):
    return db.query(scheduled_outages).filter(scheduled_outages.outage_id == id).first()

def get_scheduled_image(db: Session, id: int):
    return db.query(scheduled_images).filter(scheduled_images.image_id == id)  

def get_schedule(db: Session, id: int):
    return db.query(schedule).filter(schedule.id == id) 

# groud station schedule
def get_ground_station_request(db: Session, id: int):
    return db.query(ground_station_request).filter(ground_station_request.id == id) 
 
