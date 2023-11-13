from datetime import datetime
from Database import newmockschedule
from config.database import maintenance_order

class scheduled_activity:
    schedule_id: int
    start_time: datetime
    end_time: datetime

def schedule_activity(satellite_id: int , maintenence_request: maintenance_order):
    
    schedules = newmockschedule.get_schedule(satellite_id, maintenence_request.start_time, maintenence_request.end_time)
    
    schedule_options = []
    option = []
    
    
    list_of_activities = get_activities(schedules)
    
    rep = 0
    # each activity in schedule
    for i in range(len(list_of_activities)):
        start_of_schedule = list_of_activities[i].start_time
        last_activity = start_of_schedule # when the last last_activity ended, whether it's this request or not
        last_repetition = maintenence_request.end_time
        
        #find out how long the gap is
        if(i < len(list_of_activities)-1):
            freetime = last_activity - list_of_activities[i] # time between last activity and next one
        
        else: 
            freetime = datetime(second=0) # time until the schedule ends
            
        # start time is free
        # duration is long enough
        # there is more repeat activity to schedule
        # it can finsh before the window closes
        # *** need to check for freq_max_gap
            
        if(maintenence_request.start_time >= last_activity and freetime <= maintenence_request.duration
        and rep < maintenence_request.repetition and (last_activity + maintenence_request.duration) <= maintenence_request.end_time
        and last_repetition < last_repetition ):
            if(rep != 0):
                last_repetition = option[rep-1] + maintenence_request.duration + maintenence_request.frequency_max_gap # can not be scheduled beyond here
            
            option[rep] = last_activity                        
            last_activity = last_activity + maintenence_request.duration + maintenence_request.frequency_min_gap # can only schedule starting frome here
            
                                    
        if(rep == maintenence_request.repetition - 1):
                schedule_options.append(option)
                rep = 0
                print(option)
        else:
            if((last_activity + maintenence_request.duration) > maintenence_request.end_time):
                rep = 0
                option = []  

    return schedule_options
 
def get_activities(schedules: list): 
    list_of_activities = []
    
    # sort schedules     
    for i in range(len(schedules)):
        schedules.sort(key=lambda x: x.start_time)
    
    for j in range(len(schedules)):
        # activities = mockSchedule.get_scheduled_activity(schedules[i].schedule_id)
        
        # get all activities with that schedule_id from 3 tables from database
        image_activities = newmockschedule.get_scheduled_image(schedules[j].id)
        for i in range(len(image_activities)):
            activity = scheduled_activity(schedule_id = schedules[j].id ,start_time = image_activities[i].downlink_start, end_time = image_activities[i].dowlink_end)
            list_of_activities.append(activity)
    
        maintenence_activities = newmockschedule.get_scheduled_maintenence(schedules[j].id)
        for i in range(len(maintenence_activities)):
            activity = scheduled_activity(schedule_id = schedules[j].id , start_time = maintenence_activities[i].maintenance_start, end_time = maintenence_activities[i].maintenance_end)
            list_of_activities.append(activity)
    
            
        outage_activities = newmockschedule.get_scheduled_outage(schedules[j].id)
        for i in range(len(outage_activities)):
            activity = scheduled_activity(schedule_id = schedules[j].id , start_time = outage_activities[i].outage_start, end_time = outage_activities[i].outage_end)
            list_of_activities.append(activity)
    return list_of_activities 