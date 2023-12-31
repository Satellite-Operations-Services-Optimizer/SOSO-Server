from fastapi import APIRouter
from dotenv import dotenv_values
from config.rabbit import rabbit
from rabbit_wrapper import TopicPublisher, TopicConsumer
from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState
from config import rabbit
from rabbit_wrapper import TopicPublisher, TopicConsumer

import logging

config = dotenv_values()
logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/{satellite_id}/state")
async def stream_satellite_state(websocket: WebSocket, satellite_id: int):
    await websocket.accept()

    # tell the server you are interested in listening to satellite (so it can know to start publishing information about the satellite's state)
    publisher = TopicPublisher(rabbit(), "satellite.state.listener.create")
    publisher.publish_message({"satellite_id": satellite_id})

    # start listening to messages about the satellite's state
    consumer = TopicConsumer(rabbit(), f"satellite.state.{satellite_id}")

    await websocket.send_text("ping")

    try:
        while True:
            if satellite_state := consumer.get_message() is not None:
                await websocket.send_json(satellite_state)
            else:
                await websocket.send_text("ping") # i really can't find a way to avoid this, but it's necessary to detect when the connection is closed, cuz otherwise the WebSocketDisconnect error will never be thrown
    except WebSocketDisconnect:
        # tell server to distroy listener so it doesn't keep trying to send messages about the satellite when noone is listeneing
        publisher = TopicPublisher(rabbit(), "satellite.state.listener.destroy")
        publisher.publish_message({"satellite_id": satellite_id})