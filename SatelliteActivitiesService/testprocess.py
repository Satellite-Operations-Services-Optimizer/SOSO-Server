from config.database import  db_session
from Models.RequestModel import ActivityRequest
from Services import process, handler

request1 =  { 
            "body":
            {
        "Target": "SOSO-1",
        "Activity": "TestActivity",
        "Window": {
            "Start": "2023-11-05T00:07:00",
            "End": "2023-11-15T23:59:59"
        },
        "Duration": "100",
        "RepeatCycle": {
            "Frequency": {
            "MinimumGap": "90000",
            "MaximumGap": "91400"
            },
            "Repetition": "2"
        },
        "PayloadOutage": "TRUE"
},
            "details": {
                
            }
            }

maintenence1 =         { 
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
            "MaximumGap": "806000"
            },
            "Repetition": "3"
        },
        "PayloadOutage": "TRUE"
    },
        "details": {
                
            }
}

maintenence2 = { 
            "body":
            {
  "Target": "SOSO-1",
  "Activity": "OrbitManeuver",
  "Window": {
    "Start": "2023-10-08T06:26:47",
    "End": "2023-10-08T06:41:47"
  },
  "Duration": "900",
  "RepeatCycle": {
    "Frequency": {
      "MinimumGap": "Null",
      "MaximumGap": "Null"
    },
    "Repetition": "Null"
  },
  "PayloadOutage": "TRUE"
},
        "details": {
                
            }
}

outage1 = { 
            "body":
            {
  "Target": "ICAN",
  "Activity": "Outage",
  "Window": {
    "Start": "2023-10-08T23:00:00",
    "End": "2023-10-09T07:00:00"
  }
},
        "details": {
                
            }
}
outage2 = { 
            "body":
            {
  "Target": "SOSO-3",
  "Activity": "Outage",
  "Window": {
    "Start": "2023-10-09T10:00:00",
    "End": "2023-10-09T14:32:00"
  }
},
        "details": {
                
            }
}

print(request1["body"])

handler.handle_message(request1)
# activity_request = ActivityRequest(**request)       
# response_model = create_maintenence_request(db_session, activity_request)

# print(activity_request)