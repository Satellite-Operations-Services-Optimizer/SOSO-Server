from helpers.postgres_helper import add_image_order


def handle_message(body):
    '''
    Responsible for interacting / processing with the received messages from queue
    '''
    print("Handler function called with body: ", body)
    # Example usage of add_image_order function
    new_order_data = {
        'latitude': 34.0522,        # Replace with actual latitude
        'longitude': -118.2437,     # Replace with actual longitude
        'priority': 1,              # Set the priority level
        'image_res': 1080,          # Set the image resolution
        'image_height': 720,        # Set the image height
        'image_width': 1280         # Set the image width
    }

    add_image_order(new_order_data)
    print("Success")