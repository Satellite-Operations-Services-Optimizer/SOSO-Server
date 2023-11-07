import os
from enum import Enum
from dotenv import load_dotenv
from rabbit_wrapper import Rabbit

load_dotenv()
rabbit = Rabbit(
    host=os.getenv("RABBIT_HOST"),
    port=os.getenv("RABBIT_PORT"),
    user=os.getenv("RABBIT_USER"),
    password=os.getenv("RABBIT_PASS"),
    vhost=os.getenv("RABBIT_VHOST"),
    blocking=True
)

# enum for getting names of the services' queues
class ServiceQueues(Enum):
    RELAY_API = os.getenv("RELAY_API_QUEUE")
    IMAGE_MANAGEMENT = os.getenv("IMAGE_MANAGEMENT_QUEUE")
    SAT_ACTIVITIES = os.getenv("SAT_ACTIVITIES_QUEUE")
    SCHEDULER = os.getenv("SCHEDULER_QUEUE")
    GS_OUTBOUND = os.getenv("GS_OUTBOUND_QUEUE")

    def __str__(self):
        return str(self.value)
