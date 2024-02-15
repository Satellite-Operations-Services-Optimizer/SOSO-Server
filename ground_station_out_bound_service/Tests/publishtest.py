from rabbit_wrapper import TopicConsumer, TopicPublisher
from app_config.rabbit import rabbit


def pub():
    publisher = TopicPublisher(rabbit(), f"schedule.maintenance.create")
    publisher.publish_message("publishing to topic test")
    pass



if(__name__ == "__main__"):
    pub()
   
    