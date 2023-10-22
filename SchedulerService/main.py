from dotenv import dotenv_values
from Services.consumer import Consumer

config = dotenv_values()


def startup_event():
    print("Application Starting...")

    queue_name = str(config["SS_Consume_Queue_Name"])

    consumer = Consumer()
    consumer.consume_messages(queue=queue_name, callback=consumer.consume)


if __name__ == "__main__":
    startup_event()
