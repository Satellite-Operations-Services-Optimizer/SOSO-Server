import os
from enum import Enum
from dotenv import load_dotenv
from rabbit_wrapper import Rabbit
from typing import Optional

load_dotenv()

# get rabbitmq connection
def rabbit(blocking=True):
    if blocking: return _get_sync_connection()
    else: return _get_async_connection()

# enum for getting names of the services' queues
class ServiceQueues(Enum):
    RELAY_API = os.environ["RELAY_API_QUEUE"]
    IMAGE_MANAGEMENT = os.environ["IMAGE_MANAGEMENT_QUEUE"]
    SAT_ACTIVITIES = os.environ["SAT_ACTIVITIES_QUEUE"]
    SCHEDULER = os.environ["SCHEDULER_QUEUE"]
    GS_OUTBOUND = os.environ["GS_OUTBOUND_QUEUE"]

    def __str__(self):
        return str(self.value)

_rabbit_conn = None
def _get_sync_connection():
    global _rabbit_conn
    if _rabbit_conn is None:
        _rabbit_conn = create_rabbit_connection(blocking=True)
    return _rabbit_conn

_rabbit_conn_async = None
def _get_async_connection():
    global _rabbit_conn_async
    if _rabbit_conn_async is None:
        _rabbit_conn_async = create_rabbit_connection(blocking=False)
    return _rabbit_conn_async

def create_rabbit_connection(blocking=True):
    return Rabbit(
        host=os.environ["RABBIT_HOST"],
        port=os.environ["RABBIT_PORT"],
        user=os.environ["RABBIT_USER"],
        password=os.environ["RABBIT_PASS"],
        vhost=os.environ["RABBIT_VHOST"],
        blocking=blocking
    )
