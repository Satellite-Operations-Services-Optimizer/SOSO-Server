from config import rabbit
from rabbit_wrapper import Publisher
from fastapi.encoders import jsonable_encoder
from Models.RequestModel import RequestDetails
from Models.IMSProducerEventData import IMSProducerEventData

def publish_message_to_queue(data, request_type, destination):
    
    request_details = RequestDetails(requestType=request_type)
    message = jsonable_encoder(
        IMSProducerEventData(
            body = data,
            details = request_details
        )
    )

    print("Reached!")
    publisher = Publisher(rabbit(), destination)
    publisher.publish_message(message)