from rabbit_wrapper import Consumer
try:
    from app_config import rabbit, ServiceQueues
except ImportError as e:
    import os

    # get the absolute path of this script's immediate parent directory
    script_dir = os.path.dirname(os.path.realpath(__file__))

    # get folder structure (including immediate children folders/files) of ONLY JUST this script's IMMEDIATE parent directory as string, making sure to print nothing else, and that   we are in teh correct working directory so we don't print more folders that we need
    folder_structure = os.listdir(script_dir)
    print("\n".join(folder_structure) + "\n\n")

    #print contents of the app_config directory
    print("\n".join(os.listdir(os.path.join(script_dir, "app_config"))))





    raise Exception(str(e)+f"""

{folder_structure}
                    """)
from satellite_state.stream import setup_state_streaming_event_listeners
import logging

logger = logging.getLogger(__name__)
def startup_event():
    setup_state_streaming_event_listeners()
    consumer = Consumer(rabbit(), ServiceQueues.SCHEDULER)
    consumer.register_callback(lambda message: logger.info(f"Received message: {message}"))

    rabbit().start_consuming()


if __name__ == "__main__":
    startup_event()
