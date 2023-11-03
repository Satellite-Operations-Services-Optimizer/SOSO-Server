from dotenv import dotenv_values
from services.consumer import Consumer
from calculations.satellite import Satellite
from database import DatabaseSession
import inject

config = dotenv_values()


def startup_event():
    print("Application Starting...")
    
    db = inject.instance(DatabaseSession)
    db.query(Satellite)

    # queue_name = str(config["SS_Consume_Queue_Name"])
    #
    # consumer = Consumer()
    # consumer.consume_messages(queue=queue_name, callback=consumer.consume)


if __name__ == "__main__":
    startup_event()
