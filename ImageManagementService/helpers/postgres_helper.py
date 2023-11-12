from config.database import db_session, Base

ImageOrder = Base.classes.image_order

def add_image_order(data):
    """
    Adds a new image order to the 'image_order' table.
    :param data: A dictionary containing the data for the new image order.
    """
    try:
        new_order = ImageOrder(**data)
        
        db_session.add(new_order)
        db_session.commit()
        print("New image order added successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")
        db_session.rollback()
    finally:
        db_session.close()

