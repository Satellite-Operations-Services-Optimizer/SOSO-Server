from pathlib import Path
import json

def get_data_from_json_files(path: str, expected_keys=None):
    jsons = []
    pathlist = Path(path).glob("*.json")
    for path in pathlist:
        with path.open('r') as file:
            data = json.load(file)
            if expected_keys is not None:
                if any(key not in data for key in expected_keys):
                    raise Exception(f"Invalid JSON file at {str(path)}")
            jsons.append(data)
    return jsons