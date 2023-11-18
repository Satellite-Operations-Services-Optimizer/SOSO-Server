from datetime import datetime, timedelta
from Database import newmockschedule
from Models.RequestModel import ActivityRequest
from Database.db_curd import maintenance_order

# class scheduled_activity:
#     schedule_id: int
#     start_time: datetime
#     end_time: datetime

class scheduled_activity:
    def __init__(self, schedule_id: int, start_time: datetime, end_time: datetime):
        self.schedule_id = schedule_id
        self.start_time = start_time
        self.end_time = end_time    

class scheduling_options:
    def __init__(self, request_id: int, options: list[list[datetime]]):
        self.request_id = request_id
        self.options = options 

def schedule_activity(satellite_id: int , maintenence_request: maintenance_order):
    
    print(maintenence_request.duration)
    duration = timedelta(hours =int(maintenence_request.duration.hour),
                         minutes=int(maintenence_request.duration.minute), 
                         seconds=int(maintenence_request.duration.second))
    min_frequencey = timedelta(seconds =maintenence_request.frequency_min)
    max_frequencey = timedelta(seconds=maintenence_request.frequency_max)
    schedules = newmockschedule.get_schedule(satellite_id, maintenence_request.start_time, maintenence_request.end_time)
    
    schedule_options = []
    option = []
       
    list_of_activities = get_activities(schedules)
    end_of_schedule = list_of_activities[len(list_of_activities)-1].end_time
    last_activity = list_of_activities[0].start_time # when the last last_activity ended, whether it's this request or not
    last_repetition = maintenence_request.end_time
    nextactivity = list_of_activities[0].start_time
    with_in_frequency = True
    rep = 0
    # each activity in schedule
    for i in range(len(list_of_activities)):
        
        
        #find out how long the gap is
        if(i < len(list_of_activities)-1):
            nextactivity =  list_of_activities[i].start_time            
            freetime = nextactivity - last_activity # time between last activity and next one
            
            print(f"last activity ended at {last_activity}")
            print(f"next activity starts at {nextactivity}")
            print(f"free time number {i} is {freetime}")
            
            
        else: 
            freetime = end_of_schedule - last_activity # time until the schedule ends
            print(f"Last free time number {i} is {freetime}")
        # print(f"free time number {i} is {freetime}")  
          
        # start time or start of window is before potential start
        # duration is long enough
        # there is more repeat activity to schedule
        # it can finsh before the window closes
        # *** need to check for freq_max_gap
        
        print(f"maintenence_request.start_time is {maintenence_request.start_time}\n")
        print(f"last activity ended at {last_activity}\n")
        print(f"free time is  {freetime}\n")
        print(f"duration is {duration}\n")
        print(f"repetition - 1 is at {rep}\n")
        print(f"maintenance endtime is {maintenence_request.end_time}\n")
           
        if(maintenence_request.start_time <= last_activity and freetime >= duration
        and rep < maintenence_request.repetition and (last_activity + duration) <= maintenence_request.end_time):
            print("true")
            if(rep != 0 and len(option) >= rep): # need to check for min and max gap between the last repetition and this one
                with_in_frequency = (last_activity > last_repetition + duration + min_frequencey
                                     and last_activity < last_repetition + duration + max_frequencey)
                print(f"within freq is {with_in_frequency}\n")
            
            if(with_in_frequency):
                option.append(last_activity)
                print(f"option appended to {option}\n")
                # last_repetition = option[rep-1] + duration # when the last rep ended
                last_activity = last_activity + duration # can only schedule starting frome here
                last_repetition = last_activity
                rep += 1
            else:
                last_activity =  list_of_activities[i].end_time 
        else:
            print("false") 
            last_activity =  list_of_activities[i].end_time  
                
        if(rep == maintenence_request.repetition):
            schedule_options.append(option)
            rep = 0
            last_repetition = maintenence_request.end_time            
            print(f"options is {option}")
            print(f"schedule_options is {schedule_options}")
            option = []
        

    # possible_schedules = scheduling_options(request_id = maintenence_request.id, options = schedule_options)
    # print(possible_schedules)
    # return possible_schedules
    schedule_times = scheduling_options(request_id= maintenance_order.id, options= schedule_options)
    print(schedule_options)
    return schedule_times
 
def get_activities(schedules: list): 
    list_of_activities = []
    
    for j in range(len(schedules)):
        
        # get all activities with that schedule_id from 3 tables from database
        image_activities = newmockschedule.get_scheduled_image(schedules[j].id)
        for i in range(len(image_activities)):
            activity = scheduled_activity(schedule_id = schedules[j].id ,start_time = image_activities[i].downlink_start, end_time = image_activities[i].downlink_end)
            list_of_activities.append(activity)
    
        maintenence_activities = newmockschedule.get_scheduled_maintenence(schedules[j].id)
        for i in range(len(maintenence_activities)):
            activity = scheduled_activity(schedule_id = schedules[j].id , start_time = maintenence_activities[i].maintenance_start, end_time = maintenence_activities[i].maintenance_end)
            list_of_activities.append(activity)
    
            
        outage_activities = newmockschedule.get_scheduled_outage(schedules[j].id)
        for i in range(len(outage_activities)):
            activity = scheduled_activity(schedule_id = schedules[j].id , start_time = outage_activities[i].outage_start, end_time = outage_activities[i].outage_end)
            list_of_activities.append(activity)
            
    sorted_schedules = sorted(list_of_activities, key=lambda x: x.start_time)
    print(f"sorted activities are {sorted_schedules}")
    print("\n Activities in the Target schedules are:\n")
    
    for activity in sorted_schedules:
        print(activity.__dict__)
    return sorted_schedules 

