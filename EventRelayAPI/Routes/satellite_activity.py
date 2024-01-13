from fastapi import APIRouter
import asyncio
from dotenv import dotenv_values
from app_config.rabbit import rabbit
from rabbit_wrapper import TopicPublisher, TopicConsumer
from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState
from app_config import rabbit
from rabbit_wrapper import TopicPublisher, TopicConsumer
from models import TimeRange

import logging

config = dotenv_values()
logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{satellite_id}/outage/create")
async def create_outage(satellite_id: int, time_range: TimeRange):
    publisher = TopicPublisher(rabbit(), "satellite.outage.create")
    publisher.publish_message({"start_time": satellite_id})

@router.websocket("/{satellite_id}/state")
async def stream_satellite_state(websocket: WebSocket, satellite_id: int):
    await websocket.accept()

    # tell the server you are interested in listening to satellite (so it can know to start publishing information about the satellite's state)
    publisher = TopicPublisher(rabbit(), "satellite.state.listener.create")
    publisher.publish_message({"satellite_id": satellite_id})

    # start listening to messages about the satellite's state
    consumer = TopicConsumer(rabbit(), f"satellite.state.{satellite_id}")

    try:
        while True:
            satellite_state = consumer.get_message()
            await websocket.send_json(satellite_state or {})
    finally:
        # tell server to distroy listener so it doesn't keep trying to send messages about the satellite when noone is listeneing
        publisher = TopicPublisher(rabbit(), "satellite.state.listener.destroy")
        publisher.publish_message({"satellite_id": satellite_id})