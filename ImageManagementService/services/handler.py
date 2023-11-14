from helpers.postgres_helper import add_image_order
from helpers.rabbit_helper import publish_message_to_queue
from datetime import datetime
from config import ServiceQueues
import logging

def handle_message(body):

    print("Handler function called with body: ", body)
    
    request_data    = body.get('body')
    request_details = body.get('details')
    request_type    = request_details.get('requestType')

    if request_type == 'image-order-request':
        handle_image_orders(request_data)

   

def handle_image_orders(body):
    
    if body is None:
        logging.error("No image order data found")
        return


    # TO DO: Placeholder for FTP server interaction - This will output a list of image orders
    # ftp_image_orders = fetch_image_orders_from_ftp() 
    
    image_orders = [body]  #  Append ftp result into image_orders

    logging.info(f"Converting image orders to accepted schema: {image_orders}")

    processed_image_orders = [
        apply_image_type_settings(order.get('ImageType'), transform_request_to_db_schema(order))
        for order in image_orders 
    ]

    logging.info(f"Saving orders into database: {processed_image_orders}")

    primary_keys = [add_image_order(image) for image in processed_image_orders if image is not None]
    
    logging.info(f"Added image orders with primary keys: {primary_keys}")
    logging.info("Success")


    publish_message_to_queue(data=primary_keys,
                    request_type='image-schedule',
                    destination=ServiceQueues.IMAGE_MANAGEMENT
                    )


def transform_request_to_db_schema(request_body):    

    db_column_mapping = {
        "Latitude": "latitude",
        "Longitude": "longitude",
        "Priority": "priority",
        "ImageStartTime": "start_time",
        "ImageEndTime": "end_time",
        "DeliveryTime": "delivery_deadline",
    }

    transformed_order = {
        db_key: datetime.strptime(request_body[req_key], '%Y-%m-%dT%H:%M:%S')
        if "Time" in req_key else request_body[req_key]
        for req_key, db_key in db_column_mapping.items() if req_key in request_body
    }
    
    return transformed_order

def apply_image_type_settings(image_type, image_order):

    image_type_settings = {
        'Spotlight': {'image_res': 3, 'image_height': 10000, 'image_width': 10000},
        'Medium':    {'image_res': 2, 'image_height': 40000, 'image_width': 20000},
        'Low':       {'image_res': 1, 'image_height': 40000, 'image_width': 20000},
    }
    
    if image_type in image_type_settings:
        image_order.update(image_type_settings[image_type])
    else:
        logging.error(f"Unrecognized image type: {image_type}")
        return None
    
    return image_order
