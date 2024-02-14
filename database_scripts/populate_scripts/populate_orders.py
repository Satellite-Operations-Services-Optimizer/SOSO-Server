from database_scripts.utils import get_data_from_json_files
from pathlib import Path
from datetime import datetime, timedelta
from app_config import get_db_session
from app_config.database.mapping import ImageOrder
from app_config import logging


logger = logging.getLogger(__name__)

def populate_sample_image_orders():
    logger.info("Populating `image_orders` table with sample data...")
    image_order_jsons = get_data_from_json_files(
        Path(__file__).parent / 'sample_image_orders',
        expected_keys=[
            "Latitude",
            "Longitude",
            "Priority",
            "ImageType",
            "ImageStartTime",
            "ImageEndTime",
            "DeliveryTime",
            "Recurrence"
        ]
    )
    orders = []
    for image_order in image_order_jsons.values():
        orders.append(image_order_from_json(image_order))
    session = get_db_session()
    session.add_all(orders)
    session.commit()


def image_order_from_json(image_order_json):
    num_revisits = 0 if type(image_order_json["Recurrence"])==list else image_order_json["Recurrence"].get("NumberOfRevisits")
    visits_remaining = num_revisits+1,
    if type(image_order_json["Recurrence"]) != list:
        frequency_amount = image_order_json["Recurrence"].get("RevisitFrequency")
        frequency_unit = image_order_json["Recurrence"].get("RevisitFrequencyUnits").lower()
        revisit_frequency = timedelta(**{frequency_unit: frequency_amount})
    else:
        revisit_frequency = None
    return ImageOrder(
        latitude=image_order_json["Latitude"],
        longitude=image_order_json["Longitude"],
        priority=image_order_json["Priority"],
        image_type=parse_image_type(image_order_json["ImageType"]),
        start_time=datetime.fromisoformat(image_order_json["ImageStartTime"]),
        end_time=datetime.fromisoformat(image_order_json["ImageEndTime"]),
        delivery_deadline=datetime.fromisoformat(image_order_json["DeliveryTime"]),
        visits_remaining=visits_remaining,
        revisit_frequency=revisit_frequency
    )

def parse_image_type(request_image_type):
    type_mappings = {
        'low': 'low_res',
        'medium': 'medium_res',
        'high': 'high_res'
    }
    return type_mappings[request_image_type.lower()]