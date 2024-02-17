from image_management_service.helpers.postgres_helper import add_image_order
from image_management_service.helpers.rabbit_helper import publish_message_to_queue
from image_management_service.helpers.conversion_helper import transform_request_to_order
from image_management_service.models.RequestModel import ImageRequest
from app_config.database.mapping import ImageOrder
from pydantic import ValidationError
from datetime import datetime, timedelta
from app_config import ServiceQueues
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

    try:
        model = ImageRequest.model_validate(body)
    except ValidationError:
        return ("", -1)
    
    logging.info(f"Converting image orders to accepted schema: {body}")

    image_order = transform_request_to_order(body)

    logging.info(f"Saving orders into database: {image_order}")

    primary_key = add_image_order(image_order)

    logging.info(f"Added image orders with primary keys: {primary_key}")
    logging.info("Success")


    publish_message_to_queue(data=primary_key,
                    request_type='image-schedule',
                    destination=ServiceQueues.SCHEDULER
                    )
    
    return (image_order, primary_key)


