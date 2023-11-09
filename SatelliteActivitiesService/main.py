from dotenv import dotenv_values
from Services.consumer import Consumer
from Database.database import engine
from Database import db_schemas
config = dotenv_values()


def startup_event():
    print("Application Starting...")

    queue_name = str(config["SAS_Consume_Queue_Name"])

    consumer = Consumer()
    consumer.consume_messages(queue=queue_name, callback=consumer.consume)


if __name__ == "__main__":
    db_schemas.Base.metadata.create_all(bind=engine)
    startup_event()
