from fastapi import APIRouter
import asyncio
from dotenv import dotenv_values
from app_config.rabbit import rabbit
from rabbit_wrapper import TopicPublisher, TopicConsumer
from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState
from app_config import rabbit
from rabbit_wrapper import TopicPublisher, TopicConsumer
from datetime import datetime, timedelta

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

    ping_interval = timedelta(seconds=5)

    last_time = datetime.now()
    try:
        while True:
            satellite_state = consumer.get_message()

            if satellite_state is not None:
                await websocket.send_json(satellite_state)
            elif datetime.now() - last_time > ping_interval:
                # we need to send ping data to prevent blocking waiting for a valid satellite_state.
                # we just need some async statement (send or receive anything. we can't receive otherwise we are blocked waiting for client to send)
                # that allows the websocket to be able to check if the client has disconnected.
                # It's dumb you can't check with a method if the client is disconnected (the only way I found to do it flat-out doesn't work - it's a bug)
                # so you have to ping the client to see if it's still there, and if it's not, then you can disconnect it.
                # If you don't do this, it can never disconnect, and it will never kill the state listener (cuz it will never throw a disconnect error and reach the finally blockin)
                # and if it never disconnects, we will have a celery worker running forever for no reason, wasting resources - a resource leak
                await websocket.send_text("ping") 
                last_time = datetime.now()
    finally:
        # tell server to distroy listener so it doesn't keep trying to send messages about the satellite when noone is listeneing
        publisher = TopicPublisher(rabbit(), "satellite.state.listener.destroy")
        publisher.publish_message({"satellite_id": satellite_id})