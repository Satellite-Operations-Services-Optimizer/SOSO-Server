import requests
from fastapi.encoders import jsonable_encoder
from config.database import Base

# schedule formats not up to date, need to follow parameter description given
satschedule1 = { 
            "body":
            {
                "id": 123,
                "satellite_id": 1,
                "ground_station_id": 1,
                "asset_type": 1,
                "start_time": '2023-10-08T23:00:00',
                "end_time": '2023-10-09T23:00:00',
                "status": "scheduled"
            },
        "details": {
                
            }
}

gsschedule1 = { 
            "body":
            {
                "id": 123,
                "schedule_id": 123,
                "station_id": 1,
                "signal_acquisition": "2023-10-08T10:00:00",
                "signal_loss": "2023-10-08T10:10:00"
            },
        "details": {
                
            }
}
schedule = Base.classes.schedule

test_schedule = schedule(**(satschedule1["body"]))

def test_connection(schedule):
    
    gs_url = 'http://localhost:5000/satellite_schedule'
    
    message = jsonable_encoder(schedule)
    
    response = requests.post(gs_url, json= message)
    return response;

print(test_connection(test_schedule))
