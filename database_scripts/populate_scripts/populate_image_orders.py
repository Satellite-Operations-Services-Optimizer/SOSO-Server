from database_scripts.utils import get_data_from_json_files
from pathlib import Path
from datetime import datetime, timedelta
from app_config import get_db_session
from app_config.database.mapping import ImageOrder
from app_config import logging, rabbit
from rabbit_wrapper import TopicPublisher


logger = logging.getLogger(__name__)

def populate_image_orders(path: Path, emit=True):
    logger.info("Populating `image_orders` table with sample data...")
    image_order_jsons = get_data_from_json_files(
        path,
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
    session = get_db_session()
    for image_order in image_order_jsons.values():
        order = image_order_from_json(image_order)
        orders.append(order)
        session.add(order)
        session.commit()

    if emit:
        for order in orders:
            TopicPublisher(rabbit(), f"order.{order.order_type}.created").publish_message(order.id)


def image_order_from_json(image_order_json):
    repeat_count = 0 if type(image_order_json["Recurrence"])==list else image_order_json["Recurrence"].get("NumberOfRevisits")
    repeat_count = repeat_count or 0
    visits_remaining = (repeat_count or 0)+1
    does_not_repeat = not image_order_json["Recurrence"] or type(image_order_json["Recurrence"]) == list or image_order_json["Recurrence"]["Revisit"] == "False"
    if not does_not_repeat:
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
        repeat_count=repeat_count,
        visits_remaining=visits_remaining,
        revisit_frequency=revisit_frequency
    )

def parse_image_type(request_image_type):
    type_mappings = {
        'low': 'low',
        'medium': 'medium',
        'high': 'spotlight'
    }
    return type_mappings[request_image_type.lower()]