from rabbit_wrapper import Consumer
from app_config import rabbit as rab, ServiceQueues
from services.handler import handle_message
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from Helpers.ftp_helper import *

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()
logging.getLogger("apscheduler").propagate = False

def startup_event():
    
    scheduler.start()
    consumer = Consumer(rab(), ServiceQueues.IMAGE_MANAGEMENT)
    consumer.register_callback(callback=handle_message) # replace handle_message with whatever function you want to call whenever a message is received.
    rab().start_consuming()

@scheduler.scheduled_job('interval', seconds=5)
def timed_job():
    logging.info('[Cron Job | Pull From FTP] Running')
    imageRequests = getJSONsFromFTP()
    
    logging.info("[Cron Job | Pull From FTP: FINAL] Files To Be Considered")
    for imgReq in imageRequests:
        logging.info(str(imgReq))
        logging.info("***")
    
    for imgReq in imageRequests:
        logging.info(f"[Cron Job | Pull From FTP] Sent {str(imgReq)} to image handler")
        handle_image_orders(imgReq) 
    

if __name__ == "__main__":
    startup_event()

