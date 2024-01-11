from app_config import logging
from app_config import get_db_session
from app_config.db_classes import Satellite
from pathlib import Path
import json
import uuid


logger = logging.getLogger(__name__)

def populate_sample_satellites():
    logger.info("Populating `satellite` table with sample data...")
    path = Path(__file__).parent / 'satellite_sample_tles'
    tles = _get_tles_from_text_files(str(path))
    tles.extend(_get_tles_from_json_files(str(path)))

    satellites = []
    for tle in tles:
        name = tle.pop('name', _generate_satellite_name())
        satellites.append(
            Satellite(
                name=name,
                tle=tle,
                storage_capacity=1,
                power_capacity=1,
                fov_max=1,
                fov_min=1,
                is_illuminated=True,
                under_outage=False,
            )
        )
    
    session = get_db_session()
    session.add_all(satellites)
    session.commit()


def _get_tles_from_text_files(path: str):
    tles = []
    pathlist = Path(path).glob("*.txt")
    for path in pathlist:
        with path.open('r') as file:
            lines = file.readlines()
            if len(lines)==3:
                tles.append({
                    "name": lines[0],
                    "line1": lines[1],
                    "line2": lines[2]
                })
            elif len(lines)==2:
                tles.append({
                    "line1": lines[0],
                    "line2": lines[1]
                })
            else:
                raise Exception(f"Invalid two-line element file at {str(path)}")
    return tles

def _get_tles_from_json_files(path: str):
    tles = []
    pathlist = Path(path).glob("*.json")
    for path in pathlist:
        with path.open('r') as file:
            data = json.load(file)
            if 'line1' not in data or 'line2' not in data:
                raise Exception(f"Invalid two-line element file at {str(path)}")
            tles.append(data)
    return tles


def _generate_satellite_name():
    return f"unnamed_sat_{uuid.uuid4()}"