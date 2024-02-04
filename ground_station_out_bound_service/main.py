from apscheduler.schedulers.background import BackgroundScheduler
from rabbit_wrapper import Consumer, TopicConsumer
from app_config.rabbit import rabbit, ServiceQueues
from ground_station_out_bound_service.Services.handler import handle_maintenance, handle_imaging, handle_cancelled
from ground_station_out_bound_service.Services.routine_send import send_upcoming_contacts
from ground_station_out_bound_service.test import schedule_send
import logging

logger = logging.getLogger(__name__)

# check every 1 hour for upcoming contact
scheduler = BackgroundScheduler()
scheduler.add_job(send_upcoming_contacts, 'interval', hours=1)

#### test 
# schedulertest = BackgroundScheduler()
# schedulertest.add_job(schedule_send, 'interval', seconds=10)

def startup_event():
    
    # send schedules
    scheduler.start()
    
    # test
    # schedulertest.start()
    
    maintenance_consumer = TopicConsumer(rabbit(), f"schedule.maintenance.created")
    maintenance_consumer.bind(f"schedule.maintenance.rescheduled")
    maintenance_consumer.register_callback(callback=handle_maintenance) 
    
    imaging_consumer = TopicConsumer(rabbit(), f"schedule.image.created")
    imaging_consumer.bind(f"schedule.image.rescheduled")
    imaging_consumer.register_callback(callback=handle_imaging) 
    
    cancelled_consumer = TopicConsumer(rabbit(), f"schedule.image.cancelled")
    cancelled_consumer.register_callback(callback=handle_cancelled)
    
    cancelled_consumer = TopicConsumer(rabbit(), f"schedule.maintenance.cancelled")
    cancelled_consumer.register_callback(callback=handle_cancelled)
    
    rabbit().start_consuming()
    
    
       

if __name__ == "__main__":
    startup_event()
