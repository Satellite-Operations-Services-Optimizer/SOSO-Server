from rabbit_wrapper import TopicConsumer, TopicPublisher
from app_config.rabbit import rabbit

def handle_message(body):
    print(f"{body}")


def sub():
    consumer = TopicConsumer(rabbit(), f"schedule.maintenance.create")
    consumer.register_callback(callback=handle_message)    
    rabbit().start_consuming()
   
    pass

if(__name__ == "__main__"):
    sub()
   
    