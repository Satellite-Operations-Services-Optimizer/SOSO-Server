#deprecated methods
from fastapi import HTTPException, status
from app_config.database.setup import get_session
from app_config.database.mapping import Schedule, ScheduledImaging, ScheduledMaintenance, ScheduledOutage


def get_all_basic_schedules():
    session = get_session()
    try:
        all_schedules = session.query(Schedule).all()
        return all_schedules
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: session.close()

def get_basic_schedule_by_id(id):
    session = get_session()
    try:
        schedule = session.query(Schedule).filter(Schedule.id==id).first()

        if not schedule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Schedule with id {id} not found")
    
        return schedule
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: session.close()

# Add to_dict methods to instances of the automap classes
def schedule_to_dict(self):
    return {
        "id": self.id,
        "satellite_id": self.satellite_id,
        "ground_station_id": self.ground_station_id,
        "asset_type": self.asset_type,
        "start_time": self.start_time.isoformat(),
        "end_time": self.end_time.isoformat(),
        "status": self.status
        # Add other fields as needed
    }

def scheduled_images_to_dict(self):
    return {
        "schedule_id": self.schedule_id,
        "image_id": self.image_id,
        "request_id": self.request_id,
        "downlink_start": self.downlink_start.isoformat(),
        "downlink_end": self.downlink_end.isoformat(),
        "data_size": self.data_size,
        "schedule_type": self.schedule_type,
        "status": self.status
        # Add other fields as needed
    }

def scheduled_maintenance_to_dict(self):
    return {
        "schedule_id": self.schedule_id,
        "maintenace_id": self.maintenance_id,
        "maintenance_start": self.maintenance_start.isoformat(),
        "maintenance_end": self.maintenance_end.isoformat(),
        "repetition_number": self.repetition_number,
        "description": self.description,
        "priority": self.priority,
        "status": self.status
        # Add other fields as needed
    }

def scheduled_outages_to_dict(self):
    return {
        "schedule_id": self.schedule_id,
        "outage_id": self.outage_id,
        "outage_start": self.outage_start.isoformat(),
        "outage_end": self.outage_end.isoformat(),
        "status": self.status
        # Add other fields as needed
    }

# Add the to_dict methods to the instances of the automap classes
Schedule.to_dict = schedule_to_dict
ScheduledImaging.to_dict = scheduled_images_to_dict
ScheduledMaintenance.to_dict = scheduled_maintenance_to_dict
ScheduledOutage.to_dict = scheduled_outages_to_dict

def get_all_brute_force_joined_schedules():
    session = get_session()
    try:
        all_joined_schedules = session.query(Schedule, ScheduledImaging, ScheduledMaintenance, ScheduledOutage).\
            join(ScheduledImaging, Schedule.id == ScheduledImaging.schedule_id).\
            join(ScheduledMaintenance, Schedule.id == ScheduledMaintenance.schedule_id).\
            join(ScheduledOutage, Schedule.id == ScheduledOutage.schedule_id).\
            all()

        result_json = [
            {
                "schedule": schedule.to_dict(),
                "scheduled_images": scheduled_images.to_dict(),
                "scheduled_maintenance": scheduled_maintenance.to_dict(),
                "scheduled_outages": scheduled_outages.to_dict()
            }
            for schedule, scheduled_images, scheduled_maintenance, scheduled_outages in all_joined_schedules
        ]

        return result_json
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: session.close()

def get_all_joined_schedules():
    session = get_session()
    try:

        schedule_columns = [Schedule.id, Schedule.satellite_id, 
                            Schedule.ground_station_id, Schedule.start_time, Schedule.end_time, Schedule.status]
        
        scheduled_images_columns = [ScheduledImaging.schedule_id, 
                                    ScheduledImaging.image_id, ScheduledImaging.request_id, 
                                    ScheduledImaging.downlink_start, ScheduledImaging.downlink_end, 
                                    ScheduledImaging.data_size, ScheduledImaging.schedule_type, ScheduledImaging.status]
        
        scheduled_maintenance_columns = [ScheduledMaintenance.schedule_id, 
                                         ScheduledMaintenance.maintenance_id, ScheduledMaintenance.maintenance_start, 
                                         ScheduledMaintenance.maintenance_end, ScheduledMaintenance.repetition_number, 
                                         ScheduledMaintenance.description, ScheduledMaintenance.priority, ScheduledMaintenance.status]
        
        scheduled_outages_columns = [ScheduledOutage.schedule_id, ScheduledOutage.outage_id, 
                                     ScheduledOutage.outage_start, ScheduledOutage.outage_end, ScheduledOutage.status]


        all_joined_schedules = session.query(*schedule_columns, *scheduled_images_columns, *scheduled_maintenance_columns, *scheduled_outages_columns).\
            join(ScheduledImaging, Schedule.id == ScheduledImaging.schedule_id).\
            join(ScheduledMaintenance, Schedule.id == ScheduledMaintenance.schedule_id).\
            join(ScheduledOutage, Schedule.id == ScheduledOutage.schedule_id).\
            all()

        result_json = [
            {
                "id": schedule_id,
                "satellite_id": satellite_id,
                "ground_station_id": ground_station_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "status": status,
                "image_id": image_id,
                "maintenance_id": maintenance_id,
                "outage_id": outage_id

            }
            for schedule_id, satellite_id, ground_station_id, start_time, end_time, status, image_id, maintenance_id, outage_id, *rest_of_values in all_joined_schedules
        ]

        return {
            "status_text": "OK",
            "status_response": 201,
            "data": result_json
        }
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: session.close()

