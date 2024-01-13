from pathlib import Path
from typing import Optional
import json

def get_data_from_json_files(path: str|Path, expected_keys: Optional[list], filename_match: str="*.json", include_path_key: bool=False):
    jsons = []
    pathlist = Path(path).glob(filename_match)
    for path in pathlist:
        with path.open('r') as file:
            data = json.load(file)
            if expected_keys is not None:
                missing_keys = []
                for key in expected_keys:
                    if key not in data:
                        missing_keys.append(key)
                if len(missing_keys) > 0:
                    raise Exception(f"Invalid JSON file at {str(path)}. Expected keys not found: {missing_keys}")
            
            if include_path:
                data['file_path'] = str(path)
            jsons.append(data)
    return jsons