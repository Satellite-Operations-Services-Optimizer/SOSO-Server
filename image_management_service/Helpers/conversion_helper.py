from datetime import datetime, timedelta
from app_config.database.mapping import ImageOrder

# Get imageReq dict and return imageOrder dict
def transform_request_to_order(imageReq):
    
    imageOrder = {}
    imageOrder["latitude"] = imageReq["Latitude"];
    imageOrder["longitude"] = imageReq["Longitude"];
    imageOrder["priority"] = imageReq["Priority"];
    imageOrder["image_type"] = imageReq["ImageType"];
    imageOrder["window_start"] = imageReq["ImageStartTime"];
    imageOrder["window_end"] = imageReq["ImageEndTime"];
    imageOrder["delivery_deadline"] = imageReq["DeliveryTime"];
    
    if imageReq["Recurrence"].get("Revisit") == "True":
        freq_amount = imageReq["Recurrence"].get("RevisitFrequency")
        freq_unit = imageReq["Recurrence"].get("RevisitFrequencyUnits").lower()
        imageOrder["revisit_frequency"] = timedelta(**{freq_unit: freq_amount})
        imageOrder["number_of_visits"] = imageReq["Recurrence"].get("NumberOfRevisits") + 1
    else:
        imageOrder["revisit_frequency"] = None
        imageOrder["number_of_visits"] = 1
    
    
    return imageOrder

def transform_orderDict_to_orderDMModel(imageOrder):
    return ImageOrder(
        latitude=imageOrder["latitude"],
        longitude=imageOrder["longitude"],
        priority=imageOrder["priority"],
        image_type=parse_image_type(imageOrder["image_type"]),
        window_start=datetime.fromisoformat(imageOrder["window_start"]),
        window_end=datetime.fromisoformat(imageOrder["window_end"]),
        delivery_deadline=datetime.fromisoformat(imageOrder["delivery_deadline"]),
        number_of_visits=imageOrder["number_of_visits"],
        revisit_frequency=imageOrder["revisit_frequency"]
        );
    
def parse_image_type(request_image_type):
    type_mappings = {
        'low': 'low_res',
        'medium': 'medium_res',
        'high': 'high_res'
    }
    return type_mappings[request_image_type.lower()]