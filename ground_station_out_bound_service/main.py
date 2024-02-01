from rabbit_wrapper import Consumer, TopicConsumer
from app_config.rabbit import rabbit, ServiceQueues
from services.handler import handle_message, handle_maintenance, handle_imaging, handle_cancelled, handle_contact, send_schedules

import logging

logger = logging.getLogger(__name__)
def startup_event():
    maintenance_consumer = TopicConsumer(rabbit(), f"schedule.maintenance.created")
    maintenance_consumer.bind(f"schedule.maintenance.rescheduled")
    maintenance_consumer.register_callback(callback=handle_maintenance) 
    
    imaging_consumer = TopicConsumer(rabbit(), f"schedule.image.created")
    imaging_consumer.bind(f"schedule.image.rescheduled")
    imaging_consumer.register_callback(callback=handle_imaging) 
    
    # contact_consumer = TopicConsumer(rabbit(), f"schedule.groundstation.contact")
    # contact_consumer.register_callback(callback=handle_contact)
    
    cancelled_consumer = TopicConsumer(rabbit(), f"#.#.cancelled")
    cancelled_consumer.register_callback(callback=handle_cancelled)
    
    rabbit().start_consuming()
    
    # send schedule at some set time
    
    send_schedules();


if __name__ == "__main__":
    startup_event()
