from dotenv import dotenv_values
from pydantic import BaseModel, Field, Json
from Models.SASConsumerEventData import SASConsumerEventData
from Models.SASProducerEventData import SASProducerEventData, SASProducerEventData2
from Services.publisher import Publisher
from Helpers.BasicMessageReceiver import BasicMessageReceiver
from Models.RequestModel import ActivityRequest
from Models.ResponseModel import satellite_maintenance_request
import asyncio
import functools
from fastapi.encoders import jsonable_encoder
from fastapi import Depends
from Database.db_curd import create_maintenence_request, get_maintenence_request
from Database.db_schemas import satellite_maintenance_request as schemarequest
from Database.db_model import satellite_maintenance_request as requestmodel
import json
from datetime import timedelta
from Database.database import SessionLocal
from Services.process import schedule_activity
config = dotenv_values()


def sync(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(f(*args, **kwargs))
    return wrapper

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Consumer(BasicMessageReceiver):
    publish_queue_name = str(config["SAS_Publish_Queue_Name"])
    queue_name = str(config["SAS_Consume_Queue_Name"])
    exchange_name = str(config["Queue_Exchange_Name"])
    publisher = Publisher(publish_queue_name)

    def __init__(self):
        super().__init__()
        self.declare_queue(queue_name=self.queue_name)
        self.declare_exchange(exchange_name=self.exchange_name)
        self.bind_queue(
            exchange_name=self.exchange_name, queue_name=self.queue_name, routing_key=self.queue_name)

    @sync
    async def consume(self, channel, method, properties, body):
        body = self.decode_message(body=body)
        
        print("\nConsumedMessage: \n", body, "\n")

        request_body    = body["body"]
        request_details = body["details"]

        message = jsonable_encoder(
            SASConsumerEventData(
                message=request_body,
                details=request_details
            )
        )
        
        activity_request = ActivityRequest(**request_body)       
        
        response_model = create_maintenence_request( Depends(get_db), activity_request)

        
        print('\n from create: \n', response_model)
        
        schedule_options = schedule_activity(1, response_model)
        for i in len(schedule_options):
            print(schedule_options[i])
        # message = jsonable_encoder(
        #     SASProducerEventData(
        #         message=request_body,
        #         details=request_details
        #     )
        # )
        
       
        message2 = jsonable_encoder(
            SASProducerEventData2(
                message=response_model.__dict__,
                details=request_details # same as consumer, should maybe change
            )
        )
        
        # TODO: Add your logic here.
        #publisher = Publisher("SchedulerServiceEventData")
        # Sends sample request to EventRelayAPI's response queue
        self.publisher.publish_message(message2)
