import os
import json
import sys

def correct_json_files(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith('.json'):
                file_path = os.path.join(root, filename)
                with open(file_path, 'r') as file:
                    data = json.load(file)

                # Check if 'Revist' is in the 'Recurrence' dictionary and correct it
                if 'Recurrence' in data and 'Revist' in data['Recurrence']:
                    data['Recurrence']['Revisit'] = data['Recurrence'].pop('Revist')
                    
                    # Write the corrected data back to the file
                    with open(file_path, 'w') as file:
                        json.dump(data, file, indent=4)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    if not os.path.isdir(folder_path):
        print("The specified path is not a directory.")
        sys.exit(1)

    correct_json_files(folder_path)
    print("Completed correcting JSON files.")
