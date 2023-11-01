import logging
from typing import Dict
import msgpack
import json
import pika
from Rabbit import Rabbit

logger = logging.getLogger(__name__)


class BasicMessageSender(Rabbit):

    def encode_message(self, body: Dict, encoding_type: str = "bytes"):
        if encoding_type == "bytes":
            return msgpack.packb(body)
        else:
            raise NotImplementedError

    def send_message(
        self,
        exchange_name: str,
        routing_key: str,
        body: any,
    ):
        self.channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(body),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
        logger.debug(
            f"Sent message. Exchange: {exchange_name}, Routing Key: {routing_key}, Body: {body}"
        )
        print("Hello WOrd!")
