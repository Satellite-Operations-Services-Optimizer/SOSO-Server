from sqlalchemy.orm import Session
from pydantic import BaseModel
from pydantic import ValidationError
from satellite_activities_service.models import RequestModel
from datetime import timedelta, datetime
from satellite_activities_service.models.RequestModel import ActivityRequest

from app_config.database.mapping import Base, MaintenanceOrder, ImageOrder, OutageOrder, Satellite, GroundStation, ScheduledMaintenance, ScheduledOutage, ScheduledImaging, GroundStationRequest, Schedule 

        
def get_maintenence_request(db: Session, maintenence_id: int):
    
    return db.query(MaintenanceOrder).filter(MaintenanceOrder.id == maintenence_id).first()

def create_maintenence_request(db: Session, request: ActivityRequest):
    satellite = get_satellite_from_name(db, request.Target)
    db_request = MaintenanceOrder(
        asset_id = satellite.id,
        description=request.Activity,
        start_time=datetime.fromisoformat(request.Window.Start),
        end_time=datetime.fromisoformat(request.Window.End),
        duration=timedelta(seconds = int(request.Duration)),
        revisit_frequency=request.RepeatCycle.Repetition,
        revisit_frequency_min=request.RepeatCycle.Frequency.MinimumGap,
        revisit_frequency_max=request.RepeatCycle.Frequency.MaximumGap,        
        operations_flag=request.PayloadOutage
    )
    #db = SessionLocal() 
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    db.close()
    
    return db_request


def create_outage_request(db: Session, request: RequestModel.OutageRequest):
    satellite = get_satellite_from_name(db, request.Target)
    db_request = OutageOrder(
        asset_id = satellite.id,
        duration =  datetime.fromisoformat(request.Window.End) - datetime.fromisoformat(request.Window.Start),
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
    
    return db.query(OutageOrder).filter(OutageOrder.id == outage_id).first()

def get_image_request(db: Session, image_id: int):
    
    return db.query(ImageOrder).filter(ImageOrder.id == image_id).first()

#individual activities

def get_scheduled_maintenence(db: Session, id: int, repeat: int):
    return db.query(ScheduledMaintenance).filter(ScheduledMaintenance.manintenace_id == id).filter(ScheduledMaintenance.repeat_number == repeat)

def get_scheduled_outage(db: Session, id: int):
    return db.query(ScheduledOutage).filter(ScheduledOutage.outage_id == id).first()

## ************* needs repeat identifier ****************
def get_scheduled_image(db: Session, id: int):
    return db.query(ScheduledImaging).filter(ScheduledImaging.image_id == id)  

# statellite schedule
def get_schedule(db: Session, id: int):
    return db.query(Schedule).filter(Schedule.id == id) 

# groud station schedule
def get_ground_station_request(db: Session, id: int):
    return db.query(GroundStationRequest).filter(GroundStationRequest.id == id) 

# all activities of an order request
def get_all_repeats_from_maintenance_request(db: Session, id: int):
    return db.query(ScheduledMaintenance).filter_by(ScheduledMaintenance.maintenance_id==id).all()


## there are no repeats as of now, unique field and repeat identifier should be updated
def get_all_repeats_from_image_request(db: Session, id: int):
    return db.query(ScheduledImaging).filter_by(ScheduledImaging.image_id==id).all()
 
def get_all_schedules_in_window(db: Session, satellite_id: int, start: datetime, end: datetime):
    return db.query(Schedule).filter(Schedule.satellite_id == satellite_id).filter(Schedule.start_time >= start).filter(Schedule.end_time <= end).all()

def get_all_scheduled_images_from_schedule(db: Session, schedule_id: int):
    return db.query(ScheduledImaging).filter(ScheduledImaging.schedule_id == schedule_id).all()

def get_all_scheduled_maintenence_from_schedule(db: Session, schedule_id: int):
    return db.query(ScheduledMaintenance).filter(ScheduledMaintenance.schedule_id == schedule_id).all()

def get_all_scheduled_outage_from_schedule(db: Session, schedule_id: int):
    return db.query(ScheduledOutage).filter(ScheduledOutage.schedule_id == schedule_id).all()

def get_satellite_from_name(db: Session, satellite_name: str):
    return db.query(Satellite).filter(Satellite.name == satellite_name).first()

  