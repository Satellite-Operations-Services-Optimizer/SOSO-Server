from app_config import get_db_session, logging
from app_config.database.mapping import GroundStation
from database_scripts.utils import get_data_from_json_files
from pathlib import Path

logger = logging.getLogger(__name__)

def populate_groundstations(path: Path):
    logger.info("Populating `groundstation` table with sample data...")

    groundstation_jsons = get_data_from_json_files(
        path, 
        expected_keys=[
            "name",
            "latitude",
            "longitude",
            "elevation",
            "send_mask",
            "receive_mask",
            "uplink_rate_mbps",
            "downlink_rate_mbps"
        ],
        filename_match="*_gs.json",
    )

    groundstations = []
    for gs_json in groundstation_jsons.values():
        groundstations.append(GroundStation(**gs_json))

    session = get_db_session()
    session.add_all(groundstations)
    session.commit()
