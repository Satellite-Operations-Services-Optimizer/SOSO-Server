from config.database import db_session, Base

Schedule = Base.classes.schedule
ScheduledImages = Base.classes.scheduled_images
ScheduledMaintenance = Base.classes.scheduled_maintenance
ScheduledOutages = Base.classes.scheduled_outages

def get_all_schedules():
    
    try:
        all_schedules = db_session.query(Schedule).all()
        return all_schedules
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: db_session.close()

'''all_schedules = db_session.query(Schedule, ScheduledImages, ScheduledMaintenance, ScheduledOutages).\
            select_from(Schedule).join(ScheduledImages).join(ScheduledMaintenance).join(ScheduledOutages).all()
        return all_schedules'''