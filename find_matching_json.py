import argparse
import json
import os

def is_json_subset(subset, superset):
    """Checks if all key-value pairs in 'subset' JSON are present in 'superset' JSON."""
    if subset == superset: # Base case: if the two JSONs are equal, subset is a subset of superset
        return True
    if type(subset) is not dict or type(superset) is not dict:
        return False

    for key, value in subset.items():
        if key not in superset:
            return False
        if not is_json_subset(value, superset[key]):  # Recurse for nested structures
            return False
    return True


def find_matching_json(directory, sample_json_str):
    """Walks through a directory and its descendants to find JSON files matching a sample structure."""
    sample_json = json.loads(sample_json_str)

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        candidate_json = json.load(f)
                        if is_json_subset(sample_json, candidate_json):
                            print("Matching JSON File:", filepath)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON in file: {filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find JSON files with a matching structure")
    parser.add_argument("directory", help="The directory to search")
    parser.add_argument("sample_json", help="Sample JSON structure (as a string)")
    args = parser.parse_args()

    find_matching_json(args.directory, args.sample_json)
    # print("doing something")
    # find_matching_json('database_scripts/sample_data', '{"Latitude": 52.05670867924783, "Longitude": -88.78578030631812, "ImageType": "Low"}')
