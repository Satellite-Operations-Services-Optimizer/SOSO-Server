from fastapi.encoders import jsonable_encoder
from rabbit_wrapper import TopicConsumer, TopicPublisher
from app_config.rabbit import rabbit
from app_config import logging
from app_config.database.setup import scoped_session as db_session
from app_config.database.mapping import Base, GroundStationRequest, ScheduledContact, OutboundSchedule, ScheduledMaintenance, ScheduledImaging
from ground_station_out_bound_service.models.ScheduleModel import satellite_schedule, ground_station_request
from ground_station_out_bound_service.Helpers.contact_ground_station import send_ground_station_request, send_satellite_schedule
from ground_station_out_bound_service.Helpers.data import get_satellite, get_ground_station, update_schedule_request_status
from ground_station_out_bound_service.Helpers.util import add_maintenance_activity, add_image_activity, add_downlink_activity, add_downlink_image
from datetime import datetime

logger = logging.getLogger(__name__)

def send_upcoming_contacts():
    
    satellite_schedules = []
    ground_station_schedules = []
    current_datetime = datetime.now() 
    
    # send schedules if cantact is less than 30 minutes away
    schedule = datetime.minute(30)
    
    #possibliy multiple gs requests
    scheduled_contacts = db_session.query(ScheduledContact).filter(ScheduledContact.window_start - current_datetime > datetime.minute(5)).filter(ScheduledContact.window_start - current_datetime <= datetime.hour(schedule)).all()
    
    for contact in scheduled_contacts:
        request_ids = []
        scheduled_maintenance = db_session.query(ScheduledMaintenance).filter(ScheduledMaintenance.uplink_contact_id == contact.id).all()
        
        for maintenance in scheduled_maintenance:
            outbound_with_maintenance = add_maintenance_activity(maintenance)
            request_ids.append(maintenance.request_id)
            
        scheduled_images = db_session.query(ScheduledImaging).filter(ScheduledImaging.uplink_contact_id == contact.id).all()
        
        for imaging in scheduled_images:
            outbound_with_imaging = add_image_activity(imaging)
            outbound_with_downlink = add_downlink_activity(imaging)
            request_ids.append(imaging.request_id)
        
                  
    
        # send the satellite schedules scheduled to be uplinked at each contact
        outboundschedule = db_session.query(OutboundSchedule).filter(OutboundSchedule.contact_id == contact.id).filter(OutboundSchedule.schedule_status != "sent_to_gs").first()
        if (outboundschedule != None):
            
            if(contact.window_start - current_datetime < 0): # don't send if contact window has already passed
                logging.info(f"cannot uplink updated schedule - previous schedule has been uplinked and contact window has passed")
                failed_update = jsonable_encoder(outboundschedule)
                logging.info(f"failed update schedule: \n{failed_update}")
                
                ## publish failed update
                publisher = TopicPublisher(rabbit(), f"schedule.maintenance.create")
                publisher.publish_message("publishing to topic test")
            else:
                sat_schedule = satellite_schedule(satellite_name=outboundschedule.satellite_name,
                                                schedule_id=outboundschedule.id,
                                                activity_window=outboundschedule.activity_window,
                                                image_activities= outboundschedule.image_activities,
                                                maintenance_activities=outboundschedule.maintenance_activities,
                                                downlink_activities=outboundschedule.downlink_activities)
                sat_schedule_response = send_satellite_schedule(sat_schedule)

                if(sat_schedule_response.status_code == 200):
                    outboundschedule.schedule_status = "sent_to_gs"
                    update_schedule_request_status(request_ids, "sent_to_gs")                
                    satellite_schedules.append(outboundschedule)
                    
                    logger.info(f"Schedule {sat_schedule.schedule_id} successfully sent to ground station")
                else:
                    logger.info(f"{sat_schedule_response.status_code}: failed to send schedule {sat_schedule.schedule_id} to groundstation")
                    
        else: logger.info(f"No satellite schedules to be uplinked for contact {contact.id}")

        scheduled_downlinks = db_session.query(ScheduledImaging).filter(ScheduledImaging.downlink_contact_id == contact.id).all()
        downlink_images = []
        for downlinks in scheduled_downlinks:
            downlink_images.append(add_downlink_image(downlinks))
            
        satellite = get_satellite(contact.asset_id)
        ground_station = get_ground_station(contact.groundstation_id)
        
        gs_schedule = ground_station_request(station_name = ground_station.name,
                                             satellite = satellite.name,
                                             acquisition_of_signal=contact.window_start,
                                             loss_of_signal= contact.window_end,
                                             satellite_schedule_id=outboundschedule.id,
                                             downlink_images=downlink_images)
        gs_schedule_response = send_ground_station_request(gs_schedule)
        
        if(gs_schedule_response.status_code == 200):
            
            ground_station_schedules.append(gs_schedule)
            
            logger.info(f"ground station request contact_id:{contact.id} successfully sent to ground station")
        else:
            logger.info(f"{gs_schedule_response.status_code}: failed to send schedule contact_id:{contact.id} to groundstation")
        
    pass