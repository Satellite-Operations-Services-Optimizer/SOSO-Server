from config.database import  db_session
from Models.RequestModel import ActivityRequest
from Database.db_curd import create_maintenence_request, maintenance_order
from Services import process, handler

request =  { 
            "body":
            {
        "Target": "SOSO-1",
        "Activity": "TestActivity",
        "Window": {
            "Start": "2023-11-05T00:07:00",
            "End": "2023-11-15T23:59:59"
        },
        "Duration": "180",
        "RepeatCycle": {
            "Frequency": {
            "MinimumGap": "14000",
            "MaximumGap": "606000"
            },
            "Repetition": "2"
        },
        "PayloadOutage": "TRUE"
},
            "details": {
                
            }
            }



print(request["body"])

handler.handle_message(request)
# activity_request = ActivityRequest(**request)       
# response_model = create_maintenence_request(db_session, activity_request)

# print(activity_request)