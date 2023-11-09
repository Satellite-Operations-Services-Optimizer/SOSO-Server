from sqlalchemy.orm import Session
from pydantic import BaseModel
from pydantic import ValidationError
from Models import RequestModel
from Database.database import SessionLocal, engine
from Database import db_schemas, db_model
from datetime import timedelta, datetime
from Models.RequestModel import ActivityRequest


        
def get_maintenence_request(db: Session, maintenence_id: int):
    
    return db.query(db_schemas.satellite_maintenance_request).filter(db_schemas.satellite_maintenance_request.id == maintenence_id).first()

def create_maintenence_request(db: Session, request: ActivityRequest) -> db_model.satellite_maintenance_request:
    db_request = db_schemas.satellite_maintenance_request(
        activity_description=request.Activity,
        start_time=datetime.fromisoformat(request.Window.Start),
        end_time=datetime.fromisoformat(request.Window.End),
        duration=timedelta(seconds=int(request.Duration)),
        repetition=timedelta(seconds=int(request.RepeatCycle.Repetition)),
        frequency_min_gap=timedelta(seconds=int(request.RepeatCycle.Frequency.MinimumGap)),
        frequency_max_gap=timedelta(seconds=int(request.RepeatCycle.Frequency.MaximumGap)),        
        payload_flag=request.PayloadOutage
    )
    db = SessionLocal()
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    db.close()
    
    return db_model.satellite_maintenance_request.from_orm(db_request)  
    


def create_outage_request(maintenence_id: int, maintenance: RequestModel.ActivityRequest):
    
    
    # create maintenence model for db table and add to database
    db_maintenence = db_schemas.satellite_maintenance_request(id = maintenence_id,  start_time = maintenance.Window.Start, end_time = maintenance.Window.End,
                                                              frequency_min_gap = min_gap, frequency_max_gap = max_gap,
                                                              repetition = maintenance.RepeatCycle.Repetition, activity_description = maintenance.Activity,
                                                              duration = duration, payload_flag = maintenance.PayloadOutage)
    # db.add(db_maintenence)
    # db.commit()
    # db.refresh(db_maintenence)
    request = db_maintenence
    return db_maintenence

def get_outage_request(maintenence_id: int):
    #db = Depends(get_db)
    #return db.query(db_schemas.satellite_maintenance_request).filter(db_schemas.satellite_maintenance_request.id == maintenence_id).first()
    return request
