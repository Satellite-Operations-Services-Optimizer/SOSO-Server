from dotenv import dotenv_values
import ssl
import time
import logging
import pika
from pika.exceptions import AMQPConnectionError

logger = logging.getLogger(__name__)
config = dotenv_values()

rabbit_host = config["Rabbit_Host"],
rabbit_port = config["Rabbit_Port"],
rabbit_v_host = config["Rabbit_Virtual_Host"],
rabbit_credentials = pika.PlainCredentials(config["Rabbit_User"], config["Rabbit_Password"])


class Rabbit:
    def __init__(self):
        self.username = config["Rabbit_User"]
        self.password = config["Rabbit_Password"]
        self.host = config["Rabbit_Host"]
        self.port = config["Rabbit_Port"]
        self.protocol = "amqp"

        self._init_connection_parameters()
        self._connect()

    def _connect(self):
        tries = 0
        while True:
            try:
                self.connection = pika.BlockingConnection(self.parameters)
                self.channel = self.connection.channel()
                if self.connection.is_open:
                    break
            except (AMQPConnectionError, Exception) as e:
                time.sleep(5)
                tries += 1
                if tries == 20:
                    raise AMQPConnectionError(e)

    def _init_connection_parameters(self):
        self.credentials = pika.PlainCredentials(self.username, self.password)
        self.parameters = pika.ConnectionParameters(
            host=self.host,
            port=int(self.port),
            virtual_host="/",
            credentials=self.credentials,
            heartbeat=36000,
            connection_attempts=5
        )
        if self.protocol == "amqps":
            # SSL Context for TLS configuration of Amazon MQ for RabbitMQ
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            ssl_context.set_ciphers("ECDHE+AESGCM:!ECDSA")
            self.parameters.ssl_options = pika.SSLOptions(context=ssl_context)

    def check_connection(self):
        if not self.connection or self.connection.is_closed:
            self._connect()

    def close(self):
        self.channel.close()
        self.connection.close()

    def declare_queue(
        self, queue_name, exclusive: bool = False
    ):
        self.check_connection()
        logger.debug(f"Trying to declare queue({queue_name})...")
        self.channel.queue_declare(
            queue=queue_name,
            exclusive=exclusive,
            durable=True
        )

    def declare_exchange(self, exchange_name: str, exchange_type: str = "direct"):
        self.check_connection()
        self.channel.exchange_declare(
            exchange=exchange_name, exchange_type=exchange_type
        )

    def bind_queue(self, exchange_name: str, queue_name: str, routing_key: str):
        self.check_connection()
        self.channel.queue_bind(
            exchange=exchange_name, queue=queue_name, routing_key=routing_key
        )

    def unbind_queue(self, exchange_name: str, queue_name: str, routing_key: str):
        self.channel.queue_unbind(
            queue=queue_name, exchange=exchange_name, routing_key=routing_key
        )
