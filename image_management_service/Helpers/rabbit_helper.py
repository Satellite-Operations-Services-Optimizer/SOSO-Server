from app_config import rabbit
from rabbit_wrapper import Publisher
from fastapi.encoders import jsonable_encoder
from image_management_service.models.RequestModel import RequestDetails
from image_management_service.models.IMSProducerEventData import IMSProducerEventData

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