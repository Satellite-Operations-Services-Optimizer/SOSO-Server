
from fastapi.encoders import jsonable_encoder
from app_config import rabbit, ServiceQueues
from rabbit_wrapper import Publisher
from app_config.database.setup import get_session
from satellite_activities_service.services import process
from app_config import logging
from satellite_activities_service.models.SASConsumerEventData import SASConsumerEventData
from satellite_activities_service.models.SASProducerEventData import SASProducerScheduleOptionsData
from satellite_activities_service.models.RequestModel import ActivityRequest, OutageRequest
from satellite_activities_service.helpers.db_curd import create_maintenence_request, create_outage_request, get_satellite_from_name
import json
def handle_message(body):
    print("Handler function called!")
    # handle data storage
       
    request_body    = body["body"]
    request_details = body["details"]

    logging.info(f"Recieved {request_body}")
    
       
    session = get_session()
    try:
        not_maintenence = None
        not_outage = None

        try:
            request = ActivityRequest(**request_body)
            message_recieved = jsonable_encoder(
                SASConsumerEventData(
                    message=request,
                    details=request_details
                )
            )     
            saved_request = create_maintenence_request(session, request)
        except Exception as e:
            not_maintenence = e
            print("not maintenance: ", {e})
            
            try:
                request = OutageRequest(**request_body)     
                saved_request = create_outage_request(session, request)
                
            except Exception as e:
                not_outage = e
                print("not outage: ", {e})
                

        if not_outage and not_maintenence:
           raise ValueError("Invalid Request")

        else:
            logging.info(f"Request Saved to Database")
            
            if(type(request) == ActivityRequest):
                
                #get the satellite id from db
                satellite_id = get_satellite_from_name(session, request_body["Target"]).id
                preschedule = process.schedule_activity(satellite_id, saved_request)
        
                message = jsonable_encoder(
                    SASProducerScheduleOptionsData(
                        body=preschedule,
                        details=request_details
                    )
                )
            
                producer = Publisher(rabbit(), ServiceQueues.SCHEDULER)
                producer.publish_message(message)

    except Exception as outer_exception:
        
        print("Exception thrown: ", outer_exception)

    # if(saved_activity_request != None):
    
    #     preschedule = process.schedule_activity(request_body["Target"][5], saved_activity_request)
    
    #     logging.info(f"List of possible schedules: {preschedule.__dict__}")
    
    
    
    pass
