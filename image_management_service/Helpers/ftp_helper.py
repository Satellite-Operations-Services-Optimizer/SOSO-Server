from ftplib import FTP
import os
import json
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from Models.RequestModel import ImageRequest, ImageOrder
from dotenv import load_dotenv, find_dotenv
from typing import List
from app_config import db_session, Base
from rabbit_wrapper import Publisher, TopicPublisher, rabbit
from services.handler import handle_image_orders
import logging     

def verifyImgReqSchema(imgReq):
    try:
        currModel = ImageRequest.model_validate_json(imgReq)
        return True
    except Exception as err:
        print("[verifyImgReqSchema: EXCEPTION] " + err.json())
        return False 

def getJSONsFromFTP() -> List[ImageRequest]:
    
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
                    
                    currImgReq = ImageRequest.model_validate_json(currJSON);
                    ftpFiles.append(currImgReq)
                    
                    logging.info("[Cron Job | Pull From FTP: ADD] Added " + file + " as a potential image order")
                    
                    currFile = None
                    currJSON = None
                else:
                    logging.info("[Cron Job | Pull From FTP: IGNORE] file " + file + " did not pass the schema check.");    
                ftp.delete(file)
                logging.info("[Cron Job | Pull From FTP: DELETE] Deleting from server" + file)
                
            except Exception as error:
                logging.error("[Cron Job | Pull From FTP: IGNORE] file " + file + " is not included in the image order queue. ")
            
        
        ftp.close();
    except Exception as error:
        logging.error("[Cron Job | Pull From FTP] Exception Occurred During FTP pull: " + str(error))
        
    return ftpFiles;