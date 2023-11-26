from config.database import db_session, Base
from ftplib import FTP
import os

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
        
# def synchronizeWithFTP():
    
#     currentDirectory = os.getcwd()
#     save_directory = os.path.join(currentDirectory, 'file.json') 

#     ftp = FTP('ftp://127.0.0.1:8085');  # connect to host, default port
#     ftp.login("", "");
#     files = ftp.nlst();
#     imageRequestJsons = []
    
#     for file in files:
        
    