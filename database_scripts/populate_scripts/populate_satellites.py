from app_config import logging
from app_config import get_db_session
from app_config.database.mapping import Satellite
from pathlib import Path
from database_scripts.utils import get_data_from_json_files


logger = logging.getLogger(__name__)

def populate_sample_satellites(generage_missing_satellite_info: bool = True):
    logger.info("Populating `satellite` table with sample data...")

    sat_info_jsons = get_data_from_json_files(
        Path(__file__).parent / 'sample_satellites', 
        expected_keys=[
            "name",
            "storage_capacity",
            "power_capacity",
            "fov"
        ],
        filename_match="*_sat.json",
    )
    satellite_tles = _get_sample_satellite_tles()
    satellite_infos = {json["name"]: json for json in sat_info_jsons.values()}

    satellites = []
    for tle_path in satellite_tles:
        tle = satellite_tles[tle_path]
        satellite_name = tle.pop('name', None)

        if satellite_name in satellite_infos:
            info = satellite_infos.pop(satellite_name)
            del info['name'] # prevent multiple 'name' arguments when using spread operator
            satellites.append(
                Satellite(
                    name=satellite_name,
                    tle=satellite_tles[tle_path],
                    **info
                )
            )
        elif generage_missing_satellite_info:
            satellites.append(
                Satellite(
                    name=satellite_name,
                    tle=satellite_tles[tle_path],
                    storage_capacity=500_000_000,
                    power_capacity=1300.0,
                    fov_max=45.0,
                    fov_min=-45.0,
                )
            )
        else:
            raise Exception(f"Missing satellite info for sample_tle file at {tle_path}. Create a json file in the 'sample_satellites' folder ending in '_sat.json', containing the missing satellite information for this tle")

        satellite_infos.pop(satellite_name, None) # we have handled this satellite_info file, so remove it from the dict
    
    # Add any remaining satellites that don't have separate tle files, but have their tle defined in their json
    for satellite_name in satellite_infos:
        sat_info_path = satellite_infos[satellite_name].pop('file_path', None)
        if "tle" not in satellite_infos[satellite_name] or 'line1' not in satellite_infos[satellite_name]['tle'] or 'line2' not in satellite_infos[satellite_name]['tle']:
            raise Exception(f"Missing tle information for sample_satellite file at{sat_info_path}. Add a 'tle' key to the json file with line1 and line2 defined, or create a separate tle file with the same satellite name in the 'sample_satellites/tles' folder")
        satellites.append(
            Satellite(
                name=satellite_name,
                tle=satellite_infos[satellite_name]['tle'],
                **satellite_infos[satellite_name]
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

            satellite_name = lines.pop(0).strip() if len(lines)==3 else None
            line1 = lines[1].strip() if len(lines)==3 else lines[0]
            line2 = lines[2].strip() if len(lines)==3 else lines[1]
            tles[str(path)] = {
                "name": satellite_name,
                "line1": line1,
                "line2": line2,
            }
    return tles
