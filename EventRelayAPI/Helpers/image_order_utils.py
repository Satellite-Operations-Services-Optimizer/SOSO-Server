from app_config.database.setup import get_session, Base

ImageOrder = Base.classes.image_order

def get_image_orders():
    session = get_session()
    try:
        images_orders = session.query(ImageOrder).all()
        return {
            "status_text": "OK",
            "status_response": 201,
            "data": images_orders
        }
        
    except Exception as e:
        print("Error Occured getting Image Orders");
        return None
    
    finally:
        session.close();
        
     