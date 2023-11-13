from config.database import db_session
import process
def handle_message(body):
    print("Handler function called!")
    # handle data storage
    
    request_body    = body["body"]
    request_details = body["details"]

    message = jsonable_encoder(
        SASConsumerEventData(
            message=request_body,
            details=request_details
        )
    )
        
    activity_request = ActivityRequest(**request_body)       
    
    response_model = create_maintenence_request(db_session, activity_request)

    
    print('\n from create: \n', response_model)
    
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

def prepare_message():
    process()

