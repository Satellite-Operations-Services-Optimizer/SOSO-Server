from database_scripts.utils import get_data_from_json_files
from pathlib import Path
from datetime import datetime, timedelta
from app_config import get_db_session
from app_config.database.mapping import MaintenanceOrder, Satellite
from app_config import logging, rabbit
from rabbit_wrapper import TopicPublisher


logger = logging.getLogger(__name__)

def populate_maintenance_orders(path: Path, emit=True):
    logger.info("Populating `maintenance_order` table with sample data...")
    image_order_jsons = get_data_from_json_files(
        path,
        expected_keys=[
            "Target",
            "Activity",
            "Window",
            "Duration",
            "RepeatCycle",
            "PayloadOutage",
        ]
    )
    orders = []
    for image_order in image_order_jsons.values():
        orders.append(maintenance_order_from_json(image_order))
    session = get_db_session()
    session.add_all(orders)
    session.commit()

    if emit:
        for order in orders:
            TopicPublisher(rabbit(), f"order.{order.order_type}.created").publish_message(order.id)


def maintenance_order_from_json(maintenance_order_json):
    session = get_db_session()
    satellite = session.query(Satellite).filter_by(name=maintenance_order_json["Target"]).one()

    duration = timedelta(seconds=int(maintenance_order_json["Duration"]))

    if maintenance_order_json["RepeatCycle"]["Repetition"] == "Null":
        number_of_visits = 1
        revisit_frequency = timedelta(seconds=0)
        revisit_frequency_max = timedelta(seconds=0)
    else:
        number_of_visits = int(maintenance_order_json["RepeatCycle"]["Repetition"]) + 1
        revisit_frequency = timedelta(seconds=int(maintenance_order_json["RepeatCycle"]["Frequency"]["MinimumGap"]))
        revisit_frequency_max = timedelta(seconds=int(maintenance_order_json["RepeatCycle"]["Frequency"]["MaximumGap"]))
    payload_outage = maintenance_order_json["PayloadOutage"].lower()=="true"
    return MaintenanceOrder(
        asset_id=int(satellite.id),
        description=maintenance_order_json["Activity"],
        start_time=datetime.fromisoformat(maintenance_order_json["Window"]["Start"]),
        end_time=datetime.fromisoformat(maintenance_order_json["Window"]["End"]),
        duration=duration,
        number_of_visits=number_of_visits,
        revisit_frequency=revisit_frequency,
        revisit_frequency_max=revisit_frequency_max,
        payload_outage=payload_outage,
    )