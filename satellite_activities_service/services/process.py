from datetime import datetime, timedelta
from app_config.database.setup import get_session
from app_config.database.mapping import MaintenanceOrder
from satellite_activities_service.models.RequestModel import ActivityRequest
from satellite_activities_service.models.ResponseModel import scheduling_options
from satellite_activities_service.helpers.util import get_activities
from satellite_activities_service.helpers.db_curd import get_all_schedules_in_window, get_all_scheduled_images_from_schedule, get_all_scheduled_maintenence_from_schedule, get_all_scheduled_outage_from_schedule 

def schedule_activity(satellite_id: int , maintenence_request: MaintenanceOrder):
    time_step = maintenence_request.start_time
    timeline = []
    
    while((time_step <= maintenence_request.end_time)):
        timeline.append(time_step)
        time_step += timedelta(minutes=10)
    
    print(maintenence_request.duration)
    # duration = timedelta(hours =int(maintenence_request.duration.hour),
    #                      minutes=int(maintenence_request.duration.minute), 
    #                      seconds=int(maintenence_request.duration.second))
    duration = maintenence_request.duration
    min_frequencey = maintenence_request.revisit_frequency_min
    max_frequencey = maintenence_request.revisit_frequency_max
    
    # **********to be tested with realdata*********
    session = get_session()
    schedules = get_all_schedules_in_window(session ,satellite_id, maintenence_request.start_time, maintenence_request.end_time)
    
    schedule_options = []
    option = []
       
    list_of_activities = get_activities(schedules)
    end_of_schedule = maintenence_request.end_time
    last_activity = maintenence_request.start_time # when the last last_activity ended, whether it's this request or not
    step = maintenence_request.start_time
    last_repetition = maintenence_request.end_time
    
    if(list_of_activities):
        nextactivity = list_of_activities[0].start_time
    else:
        nextactivity = maintenence_request.end_time
    with_in_frequency = True
    rep = 0
    i = 0 # to iterate through scheduled activities
    for t in range(len(timeline)): # time window divded into ten minute segments
    # each activity in schedule
               
        if(last_activity > step):
            step = last_activity
        else:
            step = timeline[t]
        
        #find out how long the gap is
        if(i < len(list_of_activities)-1):
            nextactivity =  list_of_activities[i].start_time            
            freetime = nextactivity - step # time between last activity and next one
                      
        else: 
            freetime = end_of_schedule - step # time until the schedule ends
            
         
          
        # start time or start of window is before potential start
        # duration is long enough
        # there is more repeat activity to schedule
        # it can finsh before the window closes
        # *** need to check for freq_max_gap
        
           
        if(maintenence_request.start_time <= step and freetime >= duration
        and rep < maintenence_request.repetition and (step + duration) <= maintenence_request.end_time):
            
            if(rep != 0 and len(option) >= rep): # need to check for min and max gap between the last repetition and this one
                with_in_frequency = (step > last_repetition + duration + min_frequencey
                                     and step < last_repetition + duration + max_frequencey)
                
            
            if(with_in_frequency):
                option.append(step)
                print(f"option appended to {option}\n")
                # last_repetition = option[rep-1] + duration # when the last rep ended
                last_activity = step + duration # can only schedule starting frome here
                last_repetition = last_activity
                rep += 1
            else:
                last_activity =  nextactivity
                i += 1
        else:
            last_activity =  nextactivity  
            i += 1
        if(rep == maintenence_request.repetition):
            schedule_options.append(option)
            rep = 0
            last_repetition = maintenence_request.end_time            
            print(f"options is {option}")
            option = []
        
        

   
    schedule_times = scheduling_options(request_id= int(maintenence_request.id), options= schedule_options)
    
    print(schedule_options)
    
    return schedule_times

