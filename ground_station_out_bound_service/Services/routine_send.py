from fastapi.encoders import jsonable_encoder
from rabbit_wrapper import TopicConsumer, TopicPublisher
from app_config.rabbit import rabbit
from app_config import logging
from app_config import get_db_session
from app_config.database.mapping import Base, GroundStationRequest, ContactEvent, OutboundSchedule, ScheduledMaintenance, ScheduledImaging, Schedule, GroundStation
from ground_station_out_bound_service.models.ScheduleModel import satellite_schedule, ground_station_request
from ground_station_out_bound_service.Helpers.contact_ground_station import send_ground_station_request, send_satellite_schedule
from ground_station_out_bound_service.Helpers.data import get_satellite, get_ground_station, update_schedule_request_status
from ground_station_out_bound_service.Helpers.util import add_maintenance_activity, add_image_activity, add_downlink_activity, add_downlink_image
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)
db_session = get_db_session()

def send_upcoming_contacts():
    
    satellite_schedules = []
    ground_station_schedules = []
    current_datetime = datetime.now(timezone.utc) 
    
    # send schedules if contact is less than 20 minutes away
    schedule_limit = db_session.query(Schedule).first().rejection_cutoff
        
    gs_limit = db_session.query(GroundStation).first().reconfig_duration
    
    #possibliy multiple gs requests
    scheduled_contacts = db_session.query(ContactEvent).filter(ContactEvent.start_time - current_datetime > gs_limit).filter(ContactEvent.start_time - current_datetime <= schedule_limit).all()
    
    for contact in scheduled_contacts:
        request_ids = []
        
        
                  
    
        # send the satellite schedules scheduled to be uplinked at each contact
        outboundschedule = db_session.query(OutboundSchedule).filter(OutboundSchedule.contact_id == contact.id).first()
        
        if(outboundschedule == None):
            scheduled_maintenance = db_session.query(ScheduledMaintenance).filter(ScheduledMaintenance.uplink_contact_id == contact.id).all()
        
            for maintenance in scheduled_maintenance:
                outbound_with_maintenance = add_maintenance_activity(maintenance)
                request_ids.append(maintenance.request_id)
                
            scheduled_images = db_session.query(ScheduledImaging).filter(ScheduledImaging.uplink_contact_id == contact.id).all()
            
            for imaging in scheduled_images:
                outbound_with_imaging = add_image_activity(imaging)
                outbound_with_downlink = add_downlink_activity(imaging)
                request_ids.append(imaging.request_id)
            
            outboundschedule = db_session.query(OutboundSchedule).filter(OutboundSchedule.contact_id == contact.id).first()   
                
        if (outboundschedule != None and outboundschedule.schedule_status != "sent_to_gs" ):
            
            if(contact.start_time - current_datetime <= gs_limit): # don't send if contact window has already passed or less than 20 minutes away
                logging.info(f"cannot uplink updated schedule - previous schedule has been uplinked and contact window has passed")
                failed_update = jsonable_encoder(outboundschedule)
                logging.info(f"failed update schedule: \n{failed_update}")
                outboundschedule.schedule_status = "failed_to_send"
                
                ## publish failed update
                publisher = TopicPublisher(rabbit(), f"outbound.schedule.failed")
                publisher.publish_message("schedule not sent: time is past valid contact window")
            else:
                if(outboundschedule.image_activities == None):
                    imageactivities = []
                else:
                    imageactivities = outboundschedule.image_activities
                    
                if(outboundschedule.maintenance_activities == None):
                    maintenanceactivities = []
                else:
                    maintenanceactivities = outboundschedule.maintenance_activities
                    
                if(outboundschedule.downlink_activities == None):
                    downlinkactivities = []
                else:
                    downlinkactivities = outboundschedule.downlink_activities
                    
                
                sat_schedule = satellite_schedule(satellite_name=outboundschedule.satellite_name,
                                                schedule_id=outboundschedule.id,
                                                activity_window=outboundschedule.activity_window,
                                                image_activities= imageactivities,
                                                maintenance_activities=maintenanceactivities,
                                                downlink_activities=downlinkactivities)
                sat_schedule_response = send_satellite_schedule(sat_schedule)

                if(sat_schedule_response.status_code == 200):
                    outboundschedule.schedule_status = "sent_to_gs"
                    update_schedule_request_status(request_ids, "sent_to_gs")                
                    satellite_schedules.append(outboundschedule)
                    
                    logger.info(f"Schedule {sat_schedule.schedule_id} successfully sent to ground station")
                else:
                    logger.info(f"{sat_schedule_response.status_code}: failed to send schedule {sat_schedule.schedule_id} to groundstation")
                    
                scheduled_downlinks = db_session.query(ScheduledImaging).filter(ScheduledImaging.downlink_contact_id == contact.id).all()
                downlink_images = []
                for downlinks in scheduled_downlinks:
                    downlink_images.append(add_downlink_image(downlinks))
                    
                satellite = get_satellite(contact.asset_id)
                ground_station = get_ground_station(contact.groundstation_id)
                
                gs_schedule = ground_station_request(station_name = ground_station.name,
                                                    satellite = satellite.name,
                                                    acquisition_of_signal=contact.start_time,
                                                    loss_of_signal= contact.start_time + contact.duration,
                                                    satellite_schedule_id=outboundschedule.id,
                                                    downlink_images=downlink_images)
                gs_schedule_response = send_ground_station_request(gs_schedule)
                
                if(gs_schedule_response.status_code == 200):
                    
                    ground_station_schedules.append(gs_schedule)
                    
                    logger.info(f"ground station request contact_id:{contact.id} successfully sent to ground station")
                else:
                    logger.info(f"{gs_schedule_response.status_code}: failed to send schedule contact_id:{contact.id} to groundstation")
                    
        else: logger.info(f"No satellite schedules to be uplinked for contact {contact.id}")

        
        
    pass