from app_config import get_db_session
from app_config.database.mapping import ContactEvent, ScheduledEvent, ImageOrder, OutboundSchedule, Satellite, GroundStation, Schedule, ScheduledImaging, ScheduleRequest
from datetime import datetime, timedelta
from fastapi.encoders import jsonable_encoder
from ground_station_out_bound_service.Tests.populate_scheduled_events import create_valid_image_order_schedule
from sqlalchemy import or_
import random

session = get_db_session()

def get_approaching_scheduled_contacts():
    contacts = session.query(ContactEvent).filter(ContactEvent.start_time >= datetime.now()).filter(ContactEvent.start_time <= (datetime.now() + timedelta(minutes=29)) ).all()
    return contacts

def get_image_orders():
    orders = session.query(ImageOrder).all()
    return orders

def check_outbound_schedule(contactId: int):
    outbound_schedule = session.query(OutboundSchedule).filter(OutboundSchedule.contact_id == contactId).first()
    if (outbound_schedule != None):
        if(outbound_schedule.status == "sent_to_gs"):
            return "schedule_sent"
        else:
            return "schedule_not_sent"
    return "schedule_not_created";

def check_schedule_status():
    contacts = get_approaching_scheduled_contacts()
    schedule_sent = []        # success scenario
    schedule_not_sent = []    # should be an error
    schedule_not_created = [] # should give warning
        
    for contact in contacts:
        sent = check_outbound_schedule(contact.id)        
        if(sent == "schedule_not_sent"):
           schedule_not_sent.append([contact.id, contact])           
        if(sent == "schedule_not_created"):
           schedule_not_created.append([contact.id, contact])               
        if(sent == "schedule_sent"):
           schedule_sent.append([contact.id, contact])
    print("\nthere was no outbound_schedule created for the following contacts: \n", schedule_not_created) 
    print("\nthe outbound_schedule was marked as sent for the following contacts: \n", schedule_sent) 
    print("\nthe outbound_schedule was marked as not sent for the following contacts: \n", schedule_not_sent)
    
    return schedule_not_sent 
def cleanup():
    schedules = session.query(Schedule).filter(Schedule.group_name == "test_gsoutbound").all()
    print(jsonable_encoder(schedules))
    for schedule in schedules:
        imageorders = set()
        contacts = session.query(ContactEvent).filter(ContactEvent.schedule_id == schedule.id).all()
        print(jsonable_encoder(contacts))
        for contact in contacts:
            scheduledimages = session.query(ScheduledImaging).filter(or_(ScheduledImaging.uplink_contact_id== contact.id, ScheduledImaging.downlink_contact_id== contact.id ) ).all()
            print(scheduledimages)
            for scheduledimage in scheduledimages:
                print("\n1111\n")
                print(scheduledimage)
                schedulerequest = session.query(ScheduleRequest).filter(ScheduleRequest.id == scheduledimage.request_id).first()
                imageorder = session.query(ImageOrder).filter(ImageOrder.id == schedulerequest.order_id).first()
                imageorders.add(imageorder)
                
                
                session.delete(scheduledimage)
                session.delete(schedulerequest)
                
                
            outbound_schedule = session.query(OutboundSchedule.contact_id == contact.id).first()            
            if(outbound_schedule != None):
                session.delete(outbound_schedule)
                #outbound_schedule.delete(synchronize_session='fetch')
            
            session.delete(contact)
            #contact.delete(synchronize_session='fetch')
       
        for imageorder in imageorders:
            session.delete(imageorder)
        session.delete(schedule)
        # schedule.delete(synchronize_session='fetch')
        session.commit()

    
            
    
def initialize():
    cleanup()    
    for i in range(1,10):
      create_valid_image_order_schedule(datetime.now() + timedelta(minutes=i*3), f"testschedule {i}")
    for i in range(10,15):
      create_valid_image_order_schedule(datetime.now() + timedelta(minutes=i*3), f"testschedule {i}")


def run_test():
    initialize()

    contacts_with_schedules_not_sent  = check_schedule_status()
    if(contacts_with_schedules_not_sent != None):
        print("\nThese outbound schedules were created but not sent: \n")
        for contact in contacts_with_schedules_not_sent:
            schedule = session.query(OutboundSchedule).filter(OutboundSchedule.contact_id == contact.id).first()
            print(jsonable_encoder(schedule), "\n")  

                    
    # contacts = jsonable_encoder(get_approaching_scheduled_contacts())
    # print(contacts)

    # contacts = session.query(ContactEvent).all()
    # print(jsonable_encoder(contacts))

if __name__ == "__main__":
    run_test()