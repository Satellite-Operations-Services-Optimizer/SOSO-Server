from app_config.database.setup import scoped_session as session
from app_config.database.mapping import ContactEvent, ScheduledEvent, ImageOrder, OutboundSchedule
from datetime import datetime
from fastapi.encoders import jsonable_encoder
def get_scheduled_contacts():
    contacts = session.query(ContactEvent).filter(ContactEvent.window_start >= datetime.now(), ContactEvent.window_start <= datetime.minute(29) ).all()
    return contacts

def get_image_orders():
    orders = session.query(ImageOrder).all()
    return orders

def check_outbound_schedule(contactId: int):
    outbound_schedule = session.query(OutboundSchedule).filter(OutboundSchedule.contactId == contactId).first()
    if (outbound_schedule != None):
        if(outbound_schedule.status == "sent_to_gs"):
            return "schedule_sent"
        else:
            return "schedule_not_sent"
    return "schedule_not_created";

def check_schedule_status():
    contacts = get_scheduled_contacts()
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

contacts_with_schedules_not_sent  = check_schedule_status()
if(contacts_with_schedules_not_sent != None):
    print("\nThese outbound schedules were not sent: \n")
    for contact in contacts_with_schedules_not_sent:
        schedule = session.query(OutboundSchedule).filter(OutboundSchedule.contactId == contact.id).first()
        print(jsonable_encoder(schedule), "\n")  


orders = jsonable_encoder(get_image_orders())
print(orders)
                  
#contacts = jsonable_encoder(get_scheduled_contacts())
#print(contacts)