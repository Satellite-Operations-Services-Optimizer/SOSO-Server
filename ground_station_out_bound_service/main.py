from apscheduler.schedulers.background import BackgroundScheduler
from rabbit_wrapper import Consumer, TopicConsumer
from app_config.rabbit import rabbit, ServiceQueues
from ground_station_out_bound_service.Services.handler import handle_maintenance, handle_imaging, handle_message
from ground_station_out_bound_service.Services.routine_send import send_upcoming_contacts
import logging

logger = logging.getLogger(__name__)

# check every 1 hour for upcoming contact
scheduler = BackgroundScheduler()
scheduler.add_job(send_upcoming_contacts, 'interval', minutes=1)

#### test 
# schedulertest = BackgroundScheduler()
# schedulertest.add_job(schedule_send, 'interval', seconds=10)

def startup_event():
    
    # send schedules
    scheduler.start()
    
    # test
    # schedulertest.start()
    consumer = Consumer(rabbit(), ServiceQueues.GS_OUTBOUND)
    consumer.register_callback(callback=handle_message) # does not do anything, outbound service sends schedules routinely
    rabbit().start_consuming()
    
    
       

if __name__ == "__main__":
    startup_event()
