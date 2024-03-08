from database_scripts.utils import get_data_from_json_files
from pathlib import Path
from datetime import datetime, timedelta
from app_config import get_db_session
from app_config.database.mapping import MaintenanceOrder, Satellite, GroundStation, SatelliteOutageOrder, GroundStationOutageOrder
from app_config import logging


logger = logging.getLogger(__name__)

def populate_outage_orders(path: Path):
    logger.info("Populating `satellite_outage` and `groundstation_outage` tables with sample data...")
    image_order_jsons = get_data_from_json_files(
        path,
        expected_keys=[
            "Target",
            "Activity",
            "Window",
        ]
    )
    orders = []
    for image_order in image_order_jsons.values():
        orders.append(outage_order_from_json(image_order))
    session = get_db_session()
    session.add_all(orders)
    session.commit()


def outage_order_from_json(outage_order_json):
    session = get_db_session()
    asset = session.query(Satellite).filter_by(name=outage_order_json["Target"]).one_or_none()
    if asset is None:
        asset = session.query(GroundStation).filter_by(name=outage_order_json["Target"]).one_or_none()

    start_time= datetime.fromisoformat(outage_order_json["Window"]["Start"])
    end_time= datetime.fromisoformat(outage_order_json["Window"]["End"])
    duration = end_time-start_time

    if asset.asset_type=="satellite":
        return SatelliteOutageOrder(
            asset_id=asset.id,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
        )
    if asset.asset_type=="groundstation":
        return GroundStationOutageOrder(
            asset_id=asset.id,
            start_time=start_time,
            end_time=end_time,
            duration=duration

        )