from app_config import logging
from app_config.database.setup import scoped_session as db_session
from app_config.database.mapping import Base, GroundStationRequest, ScheduledContact, OutboundSchedule
from ground_station_out_bound_service.models.ScheduleModel import satellite_schedule, ground_station_request
from ground_station_out_bound_service.Helpers.contact_ground_station import send_ground_station_request, send_satellite_schedule
from ground_station_out_bound_service.Helpers.data import get_satellite, get_ground_station
from datetime import datetime

logger = logging.getLogger(__name__)

def send_upcoming_contacts():
    
    satellite_schedules = []
    ground_station_schedules = []
    current_datetime = datetime.now() 
    
    # send schedules every 12 hours
    schedule = datetime.hour(12)
    
    #possibliy multiple gs requests
    scheduled_contacts = db_session.query(ScheduledContact).filter(ScheduledContact.window_start - current_datetime <= datetime.hour(schedule)).all()
    
    for contact in scheduled_contacts:
        
        # send the satellite schedules scheduled to be uplinked at each contact
        outboundschedule = db_session.query(OutboundSchedule).filter(OutboundSchedule.contact_id == contact.id).filter(OutboundSchedule.schedule_status != "sent_to_gs").first()
        if (outboundschedule != None):
            
            sat_schedule = satellite_schedule(satellite_name=outboundschedule.satellite_name,
                                              schedule_id=outboundschedule.id,
                                              activity_window=outboundschedule.activity_window,
                                              image_activities= outboundschedule.image_activities,
                                              maintenance_activities=outboundschedule.maintenance_activities,
                                              downlink_activities=outboundschedule.downlink_activities)
            sat_schedule_response = send_satellite_schedule(sat_schedule)

            if(sat_schedule_response.status_code == 200):
                outboundschedule.schedule_status = "sent_to_gs"                
                satellite_schedules.append(outboundschedule)
                
                logger.info(f"Schedule {sat_schedule.schedule_id} successfully sent to ground station")
            else:
                logger.info(f"{sat_schedule_response.status_code}: failed to send schedule {sat_schedule.schedule_id} to groundstation")
                
        else: logger.info(f"No satellite schedules to be uplinked for contact {contact.id}")

        satellite = get_satellite(contact.asset_id)
        ground_station = get_ground_station(contact.groundstation_id)
        gs_schedule = ground_station_request(station_name = ground_station.name,
                                             satellite = satellite.name,
                                             acquisition_of_signal=contact.window_start,
                                             loss_of_signal= contact.window_end,
                                             satellite_schedule_id=outboundschedule.id,
                                             downlink_images=contact.downlink_images)
        gs_schedule_response = send_ground_station_request(gs_schedule)
        
        if(gs_schedule_response.status_code == 200):
            
            ground_station_schedules.append(gs_schedule)
            
            logger.info(f"ground station request contact_id:{contact.id} successfully sent to ground station")
        else:
            logger.info(f"{gs_schedule_response.status_code}: failed to send schedule contact_id:{contact.id} to groundstation")
        
    pass



