from dotenv import dotenv_values
from Models.SSConsumerEventData import SSConsumerEvenData
from Models.SSProducerEventData import SSProducerEvenData
from Services.publisher import Publisher
from Helpers.BasicMessageReceiver import BasicMessageReceiver
import asyncio
import functools
from fastapi.encoders import jsonable_encoder


config = dotenv_values()


def sync(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(f(*args, **kwargs))
    return wrapper


class Consumer(BasicMessageReceiver):
    publish_queue_name = str(config["SS_Publish_Queue_Name"])
    queue_name = str(config["SS_Consume_Queue_Name"])
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
        ss_consumer_event_data = SSConsumerEvenData(**body)

        message = jsonable_encoder(
            SSProducerEvenData(
                message=ss_consumer_event_data.message,
                details=ss_consumer_event_data.details
            )
        )

        print("\nConsumedMessage: \n", ss_consumer_event_data, "\n")

        # TODO: Add your logic here.

        # Sends sample request to EventRelayAPI's response queue
        self.publisher.publish_message(message)
