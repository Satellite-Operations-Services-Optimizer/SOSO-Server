import uuid
import json
from pathlib import Path
from config.database import db_session, Base

Satellite = Base.classes.satellite

def populate_satellites_from_sample_tles():
    path = Path(__file__).parent / 'sample_tles'
    tles = _get_tles_from_text_files(str(path))
    tles.extend(_get_tles_from_json_files(str(path)))

    satellites = []
    for tle in tles:
        satellites.append(
            Satellite(
                tle=tle,
                storage_capacity=1,
                power_capacity=1,
                fov_max=1,
                fov_min=1,
                is_illuminated=True,
                under_outage=False,
            )
        )
    db_session.add_all(satellites)
    db_session.commit()

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
                    "name": f"unnamed_sat_{uuid.uuid4()}",
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
            name = data.get('name') or _generate_satellite_name()
            if 'line1' not in data or 'line2' not in data:
                raise Exception(f"Invalid two-line element file at {str(path)}")
            tles.append({
                "name": name,
                "line1": data['line1'],
                "line2": data['line2']
            })
    return tles


def _generate_satellite_name():
    return f"unnamed_sat_{uuid.uuid4()}"