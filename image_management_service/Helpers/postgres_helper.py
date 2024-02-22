from app_config.database.setup import get_session, Base
from app_config.database.mapping import ImageOrder
from image_management_service.helpers.conversion_helper import transform_orderDict_to_orderDMModel

def add_image_order(data):
    """
    Adds a new image order to the 'image_order' table and returns the primary key of the added image order.
    :param data: A dictionary containing the data for the new image order.
    :return: The primary key of the newly added image order.
    """
    session = get_session()
    try:
        new_order = transform_orderDict_to_orderDMModel(data)
        session.add(new_order)
        session.commit()
        
        print("New image order added successfully!")
        return new_order.id  
    
    except Exception as e:
        print(f"An error occurred: {e}")
        session.rollback()
        return None
    
    finally:
        session.close()