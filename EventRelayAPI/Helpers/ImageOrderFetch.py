from config.database import db_session, Base
from sqlalchemy import select

ImageOrder = Base.classes.image_order

def get_Image_Orders():
    try:
        images = db_session.query(ImageOrder).all();
        return images;
        
    except Exception as e:
        print("Error Occured getting Image Orders");
        return None
    finally:
        db_session.close();
        
        