from config.database import db_session, Base

ImageOrder = Base.classes.image_order

def get_image_orders():
    
    try:
        print("test")
        images = db_session.query(ImageOrder).all();
        print("test")
        return images;
        
    except Exception as e:
        print("Error Occured getting Image Orders");
        return None
    
    finally:
        db_session.close();
        
     