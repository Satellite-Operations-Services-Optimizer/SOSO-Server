# from Services.server_request_service import sample_req
# from Models.ServerDataProducerEventData import ServerDataProducerEvenData
from Helpers.BasicMessageReceiver import BasicMessageReceiver
import asyncio
import functools
from Models.ServerDataConsumerEventData import ServerDataConsumerEvenData


def sync(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(f(*args, **kwargs))
        # return asyncio.get_event_loop().run_forever()

    return wrapper


class Consumer(BasicMessageReceiver):

    @sync
    async def consume(self, channel, method, properties, body):
        body = self.decode_message(body=body)
        server_data_consumer_even_data = ServerDataConsumerEvenData(**body)

        print("\nConsumedMessage: \n", server_data_consumer_even_data, "\n")

        """
        # Send a request to an API acording to the consumed message
        response = await sample_req(serverDataProducerEvenData)

        print("Response Sent To Server...\n", response)
        """
