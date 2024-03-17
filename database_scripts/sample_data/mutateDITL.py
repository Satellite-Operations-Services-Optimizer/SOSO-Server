import os
import json
from datetime import datetime, timedelta
def process_json_files(src_dir, dest_dir, change: str, number: int):
    for root, dirs, files in os.walk(src_dir):        
        for file in files:
            if file.endswith('.json') or file.endswith('.JSON'):
                
                src_file_path = os.path.join(root, file)                
                dest_file_path = src_file_path.replace(src_dir, dest_dir)
                
                directory = os.path.dirname(src_file_path)
                directory_name = os.path.basename(directory)
                

                os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
                
                with open(src_file_path, 'r') as src_file:
                    data = json.load(src_file)
                    
                    if directory_name.startswith("JSON"):
                        mutate_image_order(data, change, number)
                    else:
                        if directory_name.startswith("MaintenanceOrders"):
                            mutate_maintenance_order(data, change, number)
                        else:
                            if directory_name.startswith("Outage"):
                                mutate_outage_order(data, change, number)
                                
                    
                    with open(dest_file_path, 'w') as dest_file:
                        json.dump(data, dest_file)

def mutate_image_order(data, change:str, number):
    if(change == "date"):
        start_time = datetime.strptime(data['ImageStartTime'], "%Y-%m-%dT%H:%M:%S")
        start_time += timedelta(days=number)
        new_start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        end_time = datetime.strptime(data['ImageEndTime'], "%Y-%m-%dT%H:%M:%S")
        end_time += timedelta(days=number)
        new_end_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        delivery_time = datetime.strptime(data['DeliveryTime'], "%Y-%m-%dT%H:%M:%S")
        delivery_time += timedelta(days=number)
        new_delivery_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        data['ImageStartTime'] = new_start_time
        data['ImageEndTime'] = new_end_time
        data['DeliveryTime'] = new_delivery_time
    else: 
        if (change == "repeat"):
            recurrence = data["Recurrence"]
            if(recurrence["Revisit"] == "False"):
                recurrence = {
                    "Revisit": "True",
                    "NumberOfRevisits": number,
                    "RevisitFrequency": 6, # default frequency
                    "RevisitFrequencyUnits": "Days" # default unit
                }
            else:
                if(recurrence["Revisit"] == "True"):
                    recurrence = {
                    "Revisit": "True",
                    "NumberOfRevisits": number,
                    "RevisitFrequency": recurrence["Revisit"]["RevisitFrequency"],
                    "RevisitFrequencyUnits": recurrence["Revisit"]["RevisitFrequencyUnits"]
                }
        
            data["Recurrence"] = recurrence
                    
            
                
    return data

def mutate_maintenance_order(data, change:str, number):
    if(change == "date"):
        start_time = datetime.strptime(data['Window']['Start'], "%Y-%m-%dT%H:%M:%S")
        start_time += timedelta(days=number)
        new_start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        end_time = datetime.strptime(data['Window']['End'], "%Y-%m-%dT%H:%M:%S")
        end_time += timedelta(days=number)
        new_end_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        data['Window']['Start'] = new_start_time
        data['Window']['End'] = new_end_time
        
    else: 
        if (change == "repeat"):
            repeatCycle = data["RepeatCycle"]
            if(repeatCycle["Repetition"] == "Null"):
                repeatCycle = {
                    "Frequency": {
                    "MinimumGap": "144000", #default minimum gap
                    "MaximumGap": "216000" #default maximum gap
                    },
                    "Repetition": number
                }
            else:
                if(repeatCycle["Repetition"] != "Null"):
                    repeatCycle = {
                    "Frequency": {
                    "MinimumGap": repeatCycle["Frequency"]["MinimumGap"],
                    "MaximumGap": repeatCycle["Frequency"]["MaximumGap"]
                    },
                    "Repetition": number
                }
            data["RepeatCycle"] = repeatCycle
                
    return data

def mutate_outage_order(data, change:str, number):
    if(change == "date"):
        start_time = datetime.strptime(data['Window']['Start'], "%Y-%m-%dT%H:%M:%S")
        start_time += timedelta(days=number)
        new_start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        end_time = datetime.strptime(data['Window']['End'], "%Y-%m-%dT%H:%M:%S")
        end_time += timedelta(days=number)
        new_end_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        data['Window']['Start'] = new_start_time
        data['Window']['End'] = new_end_time
    return data

# i is the change to be made. it can be "date" or "repeat". 
# number is the number of dates to shift by or number of repeats to have.


i = "date"
number = 2
process_json_files('DITL1', f'DITL{i}{number}', i , number)
