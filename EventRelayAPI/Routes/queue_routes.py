from fastapi import APIRouter, Body, Header, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder
from dotenv import dotenv_values
from datetime import datetime
from Models.EvenRelayRequestMdoel import EventRelayRequestModel
from Models.ServerDataConsumerEventData import ServerDataConsumerEvenData
from Services.publisher import Publisher
from Models.QueueModel import QueueRequest, BasicAuth, QueueResponse, QueueDetails
import logging

config = dotenv_values()
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/send_request", response_description="Sends a message to a Service via queue",
             status_code=status.HTTP_201_CREATED)  # response_model = Queue
async def create_queue(request: Request, queue: EventRelayRequestModel = Body(...)):
    queue_json = jsonable_encoder(queue)
    print(queue_json)
    if queue_json["details"] is None:
        req_details = QueueDetails(
            requestTime=datetime.now(),
            requestOwner="server"
        )
    else:
        req_details = QueueDetails(
            requestTime=datetime.now(),
            requestOwner=queue_json["details"]["requestOwner"]
        )

    print("Request Details: ")
    print(req_details)

    message = jsonable_encoder(
        ServerDataConsumerEvenData(
            message=queue_json["message"],
            details=req_details
        )
    )

    print("Message: ")
    print(message)
    

    publisher = Publisher(queue_json["destinationServiceQueue"])

    result = publisher.publish_message(message)

    print(result)

    response = {
        "Status": status.HTTP_200_OK,
        "Message": result,
        "Data": queue_json
    }

    return response




