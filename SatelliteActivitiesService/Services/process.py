from Database import db_model, newmockschedule

def schedule_activity(satellite_id: int , maintenence_request: db_model.satellite_maintenance_request):
            schedules = newmockschedule.get_schedule(satellite_id, maintenence_request.start_time, maintenence_request.end_time)
            list_of_list_of_activities= []
            schedule_options = []
            option = []
            # sort schedules
            for i in range(len(schedules)):
                schedules.sort(key=lambda x: x.start_time)
            
            for i in range(len(schedules)):
                # activities = mockSchedule.get_scheduled_activity(schedules[i].schedule_id)
                
                # get all activities with that schedule_id from 3 tables from database
                image_activities = newmockschedule.get_scheduled_image(schedules[i].id)
                for i in range(len(image_activities)):
                    list_of_list_of_activities.append(image_activities[i])
            
                maintenence_activities = newmockschedule.get_scheduled_maintenence(schedules[i].id)
                for i in range(len(maintenence_activities)):
                    list_of_list_of_activities.append(maintenence_activities[i])
                    
                outage_activities = newmockschedule.get_scheduled_outage(schedules[i].id)
                for i in range(len(outage_activities)):
                    list_of_list_of_activities.append(outage_activities[i])
                    
                
            
            # sort activities with in schedule
            #for i in range(len(list_of_list_of_activities)):
                list_of_list_of_activities.sort(key=lambda x: x.start_time)
            
            rep = 0
            # each schedule       
            for i in range(len(list_of_list_of_activities)): 
                start_of_schedule = schedules[i].start_time
                last_activity = start_of_schedule # when the last last_activity ended, whether it's this request or not
                last_repetition = maintenence_request.end_time
                
                # each activity in schedule
                for j in range(len(list_of_list_of_activities[i])):
                    #find out how long the gap is
                    if(j < len(list_of_list_of_activities)-1):
                        freetime = last_activity - list_of_list_of_activities[i][j] # time between last activity and current one
                    
                    else: 
                        freetime = last_activity - schedules[i].end_time # time until the schedule ends
                        
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