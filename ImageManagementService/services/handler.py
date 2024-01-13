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


    image_type = body.get('ImageType')

    logging.info(f"Converting image orders to accepted schema: {body}")

    image_order = apply_image_type_settings(image_type, transform_request_to_db_schema(body))

    logging.info(f"Saving orders into database: {image_order}")

    primary_key = add_image_order(image_order)

    logging.info(f"Added image orders with primary keys: {primary_key}")
    logging.info("Success")


    publish_message_to_queue(data=primary_key,
                    request_type='image-schedule',
                    destination=ServiceQueues.SCHEDULER
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
    
    recurrence = request_body["Recurrence"]
    if recurrence["Revisit"] == "True":
        transformed_order["num_of_revisits"] = recurrence["NumberOfRevisits"]
        transformed_order["revisit_frequency"] = recurrence["RevisitFrequency"]
        transformed_order["revisit_frequency_units"] = recurrence["RevisitFrequencyUnits"]
    else:
        transformed_order["num_of_revisits"] = 0
        transformed_order["revisit_frequency"] = 0
        transformed_order["revisit_frequency_units"] = ""
        
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
