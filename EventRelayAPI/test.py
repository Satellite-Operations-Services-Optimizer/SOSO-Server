from config import rabbit, ServiceQueues
from rabbit_wrapper import Publisher


print("AAAA0\n\n")
rabbit_connection = rabbit()
print("AAAA1\n\n")
publisher = Publisher(rabbit_connection, ServiceQueues.SAT_ACTIVITIES)
print("AAAA2\n\n")
publisher.publish_message("Hello")
print("AAAA3\n\n")