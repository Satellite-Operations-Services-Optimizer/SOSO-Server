from helpers.postgres_helper import add_image_order
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

    image_orders = [body] 

    # Placeholder for FTP server interaction
    # ftp_image_orders = fetch_image_orders_from_ftp()
    # image_orders.extend(ftp_image_orders)  # Add FTP image orders if any

    primary_keys = [add_image_order(image) for image in image_orders]
    
    logging.info(f"Added image orders with primary keys: {primary_keys}")
    logging.info("Success")
    print("Success")
