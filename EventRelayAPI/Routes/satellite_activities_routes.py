from fastapi import APIRouter, Body, Depends
from fastapi.encoders import jsonable_encoder
from dotenv import dotenv_values
from Helpers.RequestValidator import validate_request_schema
from Models.ActivityRequestModel import ActivityRequest
from Models.EventRelayData import EventRelayApiMessage
from config.rabbit import rabbit, ServiceQueues
from rabbit_wrapper import Publisher, TopicPublisher, TopicConsumer
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from config import rabbit
from rabbit_wrapper import TopicPublisher, TopicConsumer
import uuid

import logging

config = dotenv_values()
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/maintenance-activity-requests")
async def handle_request(maintenance_request: ActivityRequest = Depends(lambda request_data=Body(...): validate_request_schema(request_data, ActivityRequest))):
    
    request = jsonable_encoder(maintenance_request)

    message = jsonable_encoder(
        EventRelayApiMessage(
            body=request
        )
    )

    publisher = Publisher(rabbit(), ServiceQueues.SAT_ACTIVITIES)
    publisher.publish_message(message)

    return message
    

@router.websocket("{satellite_id}/state")
async def stream_satellite_state(websocket: WebSocket, satellite_id: int):
    await websocket.accept()

    try:
        # tell the server you are interested in listening to satellite (so it can know to start publishing information about the satellite's state)
        listener_id = uuid.uuid4()
        publisher = TopicPublisher(rabbit(), "satellite.state.listener.create")
        publisher.publish_message({"id": listener_id, "satellite_id": satellite_id})

        # start listening to messages about the satellite's state
        consumer = TopicConsumer(rabbit(), f"satellite.state.{satellite_id}")
        consumer.consume_messages(lambda satellite_state: websocket.send_json(satellite_state))
    except WebSocketDisconnect:
        # tell server to distroy listener so it doesn't keep trying to send messages about the satellite when noone is listeneing
        publisher = TopicPublisher(rabbit(), "satellite.state.listener.destroy")
        publisher.publish_message({"id": listener_id})