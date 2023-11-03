import os
from helpers.BasicMessageSender import BasicMessageSender

class Publisher(BasicMessageSender):
    exchange_name = os.getenv("EVENT_RELAY_EXCHANGE")

    def __init__(self, queue_name):
        super().__init__()
        self.queue_name = queue_name
        self.declare_exchange(self.exchange_name)
        self.declare_queue(self.queue_name)
        self.bind_queue(
            self.exchange_name,
            self.queue_name,
            self.queue_name
        )

    def publish_message(self, body):
        self.send_message(
            body=body,
            exchange_name=self.exchange_name,
            routing_key=self.queue_name,
        )
