import requests
from fastapi.encoders import jsonable_encoder
from app_config.database.mapping import Base
from ground_station_out_bound_service.models.ScheduleModel import outbound_schedule, satellite_schedule, ground_station_request
from ground_station_out_bound_service.Helpers.contact_ground_station import send_ground_station_request, send_satellite_schedule
# schedule formats not up to date, need to follow parameter description given
outbound = {
  "body": {
    "contact_id": 1,
    "satellite_name": "SOSO-2",
    "activity_window": ["2024-01-01T00:00:00", "2024-01-01T01:00:00"],
    "image_activities": [
      {
        "image_id": 1,
        "type": "capture",
        "priority": "high",
        "start_time": "2024-01-01T00:10:00"
      }
    ],
    "maintenance_activities": [
      {
        "activity_id": 1,
        "description": "Software update",
        "priority": "medium",
        "start_time": "2024-01-01T00:30:00",
        "payload_flag": True,
        "duration": 900
      }
    ],
    "downlink_activities": [
      {
        "image_id": [1],
        "start_time": "2024-01-01T00:50:00",
        "downlink_stop": "2024-01-01T00:55:00"
      }
    ]
  },
  "details": {}
  }
sat_schedule = {
    "body": {
    "satellite_name": "SOSO-2",
    "schedule_id": 1,
    "activity_window": ["2024-01-01T00:00:00", "2024-01-01T01:00:00"],
    "image_activities": [
      {
        "image_id": 1,
        "type": "capture",
        "priority": "high",
        "start_time": "2024-01-01T00:10:00"
      },
      {
        "image_id": 2,
        "type": "capture",
        "priority": "high",
        "start_time": "2024-01-01T00:12:00"
      }
    ],
    "maintenance_activities": [
      {
        "activity_id": 1,
        "description": "Software update",
        "priority": "medium",
        "start_time": "2024-01-01T00:30:00",
        "payload_flag": True,
        "duration": 300
      },
      {
        "activity_id": 2,
        "description": "Software update",
        "priority": "medium",
        "start_time": "2024-01-01T00:30:00",
        "payload_flag": True,
        "duration": 300
      }
    ],
    "downlink_activities": [
      {
        "image_id": [1,2],
        "start_time": "2024-01-01T00:50:00",
        "downlink_stop": "2024-01-01T00:55:00"
      }
    ]
  },
    "details":{}
    }
gs_request = {
      "body":{
    "station_name": "GroundStation1",
    "satellite": "SOSO-2",
    "acquisition_of_signal": "2024-01-01T00:00:00",
    "loss_of_signal": "2024-01-01T01:00:00",
    "satellite_schedule_id": 1,
    "downlink_images": [
      {
        "image_id": 12,
        "duration_of_downlink": 300,
        "size_of_image": 1.5
      }
    ]
  },
      "details": {}
}

test_schedule1 = satellite_schedule(**(sat_schedule["body"]))
#test_schedule2 = outbound_schedule(**(outbound["body"])) outbound schedule only to be stored in db not to be sent
test_schedule3 = ground_station_request(**(gs_request["body"]))

def test_connection(schedule):
    
    response = send_satellite_schedule(schedule)
    return response;

# print(test_connection(test_schedule1))

def test_connection_gs(schedule):
    
    response = response = send_ground_station_request(schedule)
    return response;

def test_schedule_send():
    
    print("\n Satellite Schedule: ", test_connection(test_schedule1), "\n")
    print("\nGround Station Schedule: ", test_connection_gs(test_schedule3), "\n\n")  

# print("\n\n", test_connection_gs(test_schedule3), "\n\n")
