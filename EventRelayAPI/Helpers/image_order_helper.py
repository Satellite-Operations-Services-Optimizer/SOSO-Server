from config.database import db_session, Base

ImageOrder = Base.classes.image_order

def get_image_orders():
    
    try:
        images_orders = db_session.query(ImageOrder).all();
        return {
            "status_text": "OK",
            "status_response": 201,
            "data": images_orders
        }
        
    except Exception as e:
        print("Error Occured getting Image Orders");
        return None
    
    finally:
        db_session.close();
        
     