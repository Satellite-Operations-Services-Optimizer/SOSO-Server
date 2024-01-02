from rabbit_wrapper import Consumer
from config.rabbit import rabbit, ServiceQueues
from services.handler import handle_message
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from helpers.ftp_helper import *

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()
logging.getLogger("apscheduler").propagate = False

def startup_event():
    
    scheduler.start()
    consumer = Consumer(rabbit(), ServiceQueues.IMAGE_MANAGEMENT)
    consumer.consume_messages(callback=handle_message) # replace handle_message with whatever function you want to call whenever a message is received.
    

@scheduler.scheduled_job('interval', seconds=10)
def timed_job():
    
    print("[FTP Started]")
    # print('[FTP] Running')
    # imageOrders = getJSONsFromFTP()
    
    # print("[FTP: FINAL] Files To Be Considered")
    # for file in imageOrders:
    #     print(file)
    #     print("***")
    
    # imageOrderIDs = addImgReqsToDB(imageOrders)
    # sendMessagesToScheduler(imageOrderIDs)
    # for id in imageOrderIDs:
    #     print(id)
    #     print("***")

if __name__ == "__main__":
    startup_event()

