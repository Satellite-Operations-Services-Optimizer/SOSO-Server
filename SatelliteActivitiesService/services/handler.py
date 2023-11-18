from config.database import db_session
from Services import process
from config import logging
from Models import SASConsumerEventData, SASProducerEventData
from Models.RequestModel import ActivityRequest, OutageRequest
from Database.db_curd import create_maintenence_request
import json
def handle_message(body):
    print("Handler function called!")
    # handle data storage
       
    request_body    = body["body"]
    request_details = body["details"]

    logging.info(f"Recieved {request_body}")
    
    # SASConsumerEventData(
    #     message=request_body,
    #     details=request_details
    # )
    # message = jsonable_encoder(
    #     SASConsumerEventData(
    #         message=request_body,
    #         details=request_details
    #     )
    # )
    
    
    # try: {    
    #     activity_request = ActivityRequest(**request_body)     
    #     response_model = create_maintenence_request(db_session, activity_request)
    # } catch Exception e {
    #     print({e})
    #     logging.info({e})
    # }

    # try: {    
    #     outage_request = OutageRequest(**request_body)     
    #     response_model = create_outage_request(db_session, outage_request)
    # } catch Exception e {
    #     print({e})
    #     logging.info({e})
    # }
    
    activity_request = ActivityRequest(**request_body)     
    response_model = create_maintenence_request(db_session, activity_request)
    
    print('\n from create: \n', response_model)
    
    preschedule = process.schedule_activity(request_body["Target"][5], response_model)
    
    print(preschedule)
    # schedule_options = schedule_activity(1, response_model)
    # for i in len(schedule_options):
    #     print(schedule_options[i])
    # # message = jsonable_encoder(
    # #     SASProducerEventData(
    # #         message=request_body,
    # #         details=request_details
    # #     )
    # # )
    
    
    # message2 = jsonable_encoder(
    #     SASProducerEventData2(
    #         message=response_model.__dict__,
    #         details=request_details # same as consumer, should maybe change
    #     )
    # )
    
    # # TODO: Add your logic here.
    # #publisher = Publisher("SchedulerServiceEventData")
    # # Sends sample request to EventRelayAPI's response queue
    # self.publisher.publish_message(message2)

    # process.schedule_activity()
    pass

# def prepare_message():