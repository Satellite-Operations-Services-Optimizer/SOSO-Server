from app_config import get_db_session, logging
from app_config.db_classes import GroundStation
from database_scripts.utils import get_data_from_json_files
from pathlib import Path

logger = logging.getLogger(__name__)

def populate_sample_groundstations():
    logger.info("Populating `groundstation` table with sample data...")

    groundstation_jsons = get_data_from_json_files(
        Path(__file__).parent / 'sample_groundstations', 
        expected_keys=[
            "name",
            "latitude",
            "longitude",
            "elevation",
            "send_mask",
            "receive_mask",
            "uplink_rate",
            "downlink_rate"
        ],
        filename_match="*_gs.json",
    )

    groundstations = []
    for gs_json in groundstation_jsons:
        groundstations.append(GroundStation(**gs_json))

    session = get_db_session()
    session.add_all(groundstations)
    session.commit()
