from ftplib import FTP
import os
import json
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from Models.RequestModel import ImageRequest, ImageOrder
from dotenv import load_dotenv, find_dotenv
from typing import List
from config.database import db_session, Base
from rabbit_wrapper import Publisher, TopicPublisher, rabbit
from services.handler import handle_image_orders
import logging 

def handOverToIMGManagement(imageRequests: List[ImageRequest]):
    for imgReq in imageRequests:
        print('[FTP] ')
        logging.info(f"[FTP | HandOverToImgManagement] Sent {imgReq} to image handler")
        handle_image_orders(imgReq)
    
    

# def addImgReqsToDB(imageOrders: List[ImageRequest]) -> List[int]:
#     imageOrderIDs = []
#     if imageOrders != None and len(imageOrders) > 0:
#         for imgOrder in imageOrders:
#             try: 
#                 db_session.add(imgOrder)
#                 db_session.commit()
#                 imgOrder = db_session.refresh(imgOrder)
#                 imageOrderIDs.append(imgOrder.id);
#                 print("[FTP] Added image order " + imgOrder.id + " to the db.")
#             except Exception as err:
#                 print("[FTP] Failed to insert into database." + str(err))
#     return imageOrderIDs    

def verifyImgReqSchema(imgReq):
    try:
        currModel = ImageRequest.model_validate_json(imgReq)
        return True
    except Exception as err:
        print("[verifyImgReqSchema: EXCEPTION] " + err.json())
        return False 

def getJSONsFromFTP() -> List[str]:
    
    ftpFiles = []
    imageRequests = []
    
    try:
        currentDirectory = os.getcwd()
        save_directory = os.path.join(currentDirectory, 'file.json') 

        load_dotenv("../../.env");
        
        FTPLink = os.getenv('FTP_LINK')
        FTPPort = int(os.getenv('FTP_PORT'))
        
        # Setting up connection to mock FTP server
        ftp = FTP();
        ftp.connect(FTPLink, FTPPort);
        ftp.login("","")
        ftp.set_pasv(False);
        ftp.set_debuglevel(1)
        ftp.set_debuglevel(0);
        # Retrieving list of file names in the FTP server
        fileList = ftp.nlst();
        
        # Accessing each file and filtering out the faulty ones
        for file in fileList:
            currFile = None;
            
            try:
                with open("sample.json", "wb") as currentFile:
                    downloadedFile = ftp.retrbinary(f"RETR {file}", currentFile.write);
                    
                with open("sample.json", "r") as currentFile:
                    currFile = (json.load(currentFile));
                    currJSON = json.dumps(currFile);
                
                if currJSON != None and verifyImgReqSchema(currJSON):
                    
                    # currImgReq = ImageRequest.model_validate_json(currJSON);
                    ftpFiles.append(currJSON)
                    logging.info("[FTP: ADD] Added " + file + " as a potential image order")
                    currFile = None
                    currJSON = None
                else:
                    logging.info("[FTP: IGNORE] file " + file + " did not pass the schema check.");    
                # ftp.delete(file)
                # print("[FTP: DELETE] Deleting from server" + file)
                
            except Exception as error:
                logging.error("[FTP: IGNORE] file " + file + " is not included in the image order queue. ")
            
        
        ftp.close();
    except Exception as error:
        logging.error("[FTP] Exception Occurred During FTP pull: " + str(error))
        
    return ftpFiles;