from config.database import db_session, Base
from sqlalchemy import select

ImageOrder = Base.classes.image_order

def get_Image_Orders():
    try:
        statement = select(ImageOrder);
        result = db_session.execute(statement);
        returnable = db_session.scalars(result).all();
        return returnable;
        
    except Exception as e:
        print("Error Occured getting Image Orders");
        return None
    finally:
        db_session.close();
        
        