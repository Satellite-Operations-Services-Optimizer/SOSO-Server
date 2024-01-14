from app_config import logging
from app_config import get_db_session
from app_config.database.mapping import Satellite
from pathlib import Path
from database_scripts.utils import get_data_from_json_files
import json
import uuid


logger = logging.getLogger(__name__)

def populate_sample_satellites(generage_missing_satellite_info: bool = True):
    logger.info("Populating `satellite` table with sample data...")

    sat_info_jsons = get_data_from_json_files(
        Path(__file__).parent / 'sample_satellites', 
        expected_keys=["name", "storage_capacity", "power_capacity", "fov_min", "fov_max"],
        filename_match="*_sat.json",
        include_path_key=True
    )
    sat_info = {json["name"]: json for json in sat_info_jsons}
    satellite_tles = _get_sample_satellite_tles()

    satellites = []
    for satellite_name in satellite_tles:
        tle_path = satellite_tles[satellite_name].pop('file_path', None)
        _ = sat_info[satellite_name].pop('file_path', None)
        if satellite_name in sat_info:
            satellites.append(
                Satellite(
                    name=satellite_name,
                    tle=satellite_tles[satellite_name],
                    **sat_info[satellite_name]
                )
            )
        else:
            if not generage_missing_satellite_info:
                raise Exception(f"Missing satellite info for sample_tle file at {tle_path}. Create a json file in the 'sample_satellites' folder ending in '_sat.json', containing the missing satellite information for this tle")
            satellites.append(
                Satellite(
                    name=satellite_name,
                    tle=satellite_tles[satellite_name],
                    storage_capacity=1,
                    power_capacity=1,
                    fov_max=1,
                    fov_min=1,
                )
            )

        sat_info.pop(satellite_name, None) # we have handled this satellite_info file, so remove it from the dict
    
    # Add any remaining satellites that don't have separate tle files, but have their tle defined in their json
    for satellite_name in sat_info:
        sat_info_path = sat_info[satellite_name].pop('file_path', None)
        if "tle" not in sat_info[satellite_name]:
            raise Exception(f"Missing tle information for sample_satellite file at{sat_info_path}. Add a 'tle' key to the json file, or create a separate tle file with the same satellite name in the 'sample_satellites/tles' folder")
        satellites.append(
            Satellite(
                name=satellite_name,
                tle=sat_info[satellite_name]['tle'],
                **sat_info[satellite_name]
            )
        )

    session = get_db_session()
    session.add_all(satellites)
    session.commit()


def _get_sample_satellite_tles():
    path = Path(__file__).parent / 'sample_satellites' / 'tles'
    tles = dict()
    pathlist = Path(path).glob("*.txt")
    for path in pathlist:
        with path.open('r') as file:
            lines = file.readlines()
            if len(lines)!=2 and len(lines)!=3:
                raise Exception(f"Invalid two-line element file at {str(path)}")

            satellite_name = lines.pop(0) if len(lines)==3 else _generate_satellite_name()
            tles[satellite_name] = {
                "name": satellite_name,
                "line1": lines[0],
                "line2": lines[1],
                "file_path": str(path)
            }
    return tles


def _generate_satellite_name():
    return f"unnamed_sat_{uuid.uuid4()}"