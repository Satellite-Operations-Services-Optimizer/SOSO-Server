from sqlalchemy.orm import Session
from pydantic import BaseModel
from pydantic import ValidationError
from models import RequestModel
from datetime import timedelta, datetime
from models.RequestModel import ActivityRequest

from app_config.database.setup import get_session
from app_config.database.mapping import Base

outage_order = Base.classes.outage_order
maintenance_order = Base.classes.maintenance_order
image_order = Base.classes.image_order
schedule = Base.classes.schedule
schedule_request = Base.classes.schedule_request
scheduled_images = Base.classes.scheduled_imaging
scheduled_maintenance = Base.classes.scheduled_maintenance
scheduled_outages = Base.classes.scheduled_outage
satellite = Base.classes.satellite
ground_station = Base.classes.ground_station
ground_station_request = Base.classes.ground_station_request

        
def get_maintenence_request(db: Session, maintenence_id: int):
    
    return db.query(maintenance_order).filter(maintenance_order.id == maintenence_id).first()

def create_maintenence_request(db: Session, request: ActivityRequest):
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


def create_outage_request(db: Session, request: RequestModel.OutageRequest):
    
    db_request = outage_order(
        asset_name = request.Target,
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
    
    session = get_session()
    
    for parent_order in session.query(image_order).all():
    # If the order has revisits, create child orders
        recurrence = parent_order.recurrence
        revisit = recurrence.get('Revisit', False)
        number_of_revisits = int(recurrence.get('NumberOfRevisits', 0))
        revisit_frequency = int(recurrence.get('RevisitFrequency', 0))
        revisit_frequency_units = recurrence.get('RevisitFrequencyUnits', 'Days')

    # Convert times to datetime objects
    image_start_time = parent_order.image_start_time
    image_end_time = parent_order.image_end_time
    delivery_time = parent_order.delivery_time

    # Calculate duration
    duration = image_end_time - image_start_time

    # Determine revisit frequency in the correct units
    if revisit_frequency_units == 'Days':
        revisit_frequency = timedelta(days=revisit_frequency)
    elif revisit_frequency_units == 'Hours':
        revisit_frequency = timedelta(hours=revisit_frequency)
    elif revisit_frequency_units == 'Weeks':
        revisit_frequency = timedelta(weeks=revisit_frequency)

    # Create the parent order
    parent_order = image_order(
        start_time=image_start_time,
        end_time=image_end_time,
        duration=duration,
        delivery_deadline=delivery_time,
        visit_count=number_of_revisits if revisit else 1,
        revisit_frequency=revisit_frequency,
        priority=parent_order.priority
    )

    # session.add(parent_order)
    # session.commit()

    # Create child orders if necessary
    if revisit:
        for i in range(number_of_revisits):
            # Calculate the new times
            new_start_time = image_start_time + (i + 1) * revisit_frequency
            new_end_time = image_end_time + (i + 1) * revisit_frequency
            new_delivery_time = delivery_time + (i + 1) * revisit_frequency

            child_order = schedule_request(
                schedule_id=parent_order.id,
                window_start=new_start_time,
                window_end=new_end_time,
                duration=duration,
                delivery_deadline=new_delivery_time
            )

            session.add(child_order)

        session.commit()

    if parent_order.number_of_revisits > 1:
        for i in range(1, parent_order.number_of_revisits):

            # Create a child order
            child_order = schedule_request(
                order_id=parent_order.id,
                window_start=parent_order.start_time,
                window_end=parent_order.end_time,
                duration=parent_order.duration,
                delivery_deadline=parent_order.delivery_deadline
            )

            # Calculate the new times
            parent_order.start_time = parent_order.start_time + i * parent_order.revisit_frequency
            parent_order.end_time = parent_order.end_time + i * parent_order.revisit_frequency
            parent_order.delivery_deadline = parent_order.delivery_deadline + i * parent_order.revisit_frequency

            # Add the child order to the session
            session.add(child_order)
        session.commit()
    return db.query(image_order).filter(image_order.id == image_id).first()

#individual activities

def get_scheduled_maintenence(db: Session, id: int, repeat: int):
    return db.query(scheduled_maintenance).filter(scheduled_maintenance.manintenace_id == id).filter(scheduled_maintenance.repeat_number == repeat)

def get_scheduled_outage(db: Session, id: int):
    return db.query(scheduled_outages).filter(scheduled_outages.outage_id == id).first()

## ************* needs repeat identifier ****************
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
    return db.query(scheduled_maintenance).filter_by(scheduled_maintenance.maintenance_id==id).all()


## there are no repeats as of now, unique field and repeat identifier should be updated
def get_all_repeats_from_image_request(db: Session, id: int):
    return db.query(scheduled_images).filter_by(scheduled_images.image_id==id).all()
 
def get_all_schedules_in_window(db: Session, satellite_id: int, start: datetime, end: datetime):
    return db.query(schedule).filter(schedule.satellite_id == satellite_id).filter(schedule.start_time >= start).filter(schedule.end_time <= end).all()

def get_all_scheduled_images_from_schedule(db: Session, schedule_id: int):
    return db.query(scheduled_images).filter(scheduled_images.schedule_id == schedule_id).all()

def get_all_scheduled_maintenence_from_schedule(db: Session, schedule_id: int):
    return db.query(scheduled_maintenance).filter(scheduled_maintenance.schedule_id == schedule_id).all()

def get_all_scheduled_outage_from_schedule(db: Session, schedule_id: int):
    return db.query(scheduled_outages).filter(scheduled_outages.schedule_id == schedule_id).all()

def get_satellite_from_name(db: Session, satellite_name: str):
    return db.query(satellite).filter(satellite.name == satellite_name).first()