from utils import get_data_from_json_files
from pathlib import Path
from datetime import datetime
from app_config import get_db_session
from app_config.db_tables import ImageOrder
from app_config import logging


logger = logging.getLogger(__name__)

def populate_sample_image_orders():
    logger.info("Populating `image_orders` table with sample data...")
    image_order_jsons = get_data_from_json_files(Path(__file__).parent / 'sample_image_orders')
    orders = []
    for order in image_order_jsons:
        orders.append(image_order_from_json(order))
    session = get_db_session()
    session.add_all(orders)
    session.commit()


def image_order_from_json(image_order_json):
    return ImageOrder(
        latitude=image_order_json["Latitude"],
        longitude=image_order_json["Longitude"],
        priority=image_order_json["Priority"],
        image_type=image_order_json["ImageType"],
        start_time=datetime.fromisoformat(image_order_json["ImageStartTime"]),
        end_time=datetime.fromisoformat(image_order_json["ImageEndTime"]),
        delivery_deadline=datetime.fromisoformat(image_order_json["DeliveryTime"]),
        num_of_revisits=None if type(image_order_json["Recurrence"])==list else image_order_json["Recurrence"].get("NumberOfRevisits"),
        revisit_frequency=None if type(image_order_json["Recurrence"])==list else image_order_json["Recurrence"].get("RevisitFrequency"),
        revisit_frequency_units=None if type(image_order_json["Recurrence"])==list else image_order_json["Recurrence"].get("RevisitFrequencyUnits")
    )