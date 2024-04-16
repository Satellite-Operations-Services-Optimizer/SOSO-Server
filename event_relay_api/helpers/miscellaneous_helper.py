import json


def tle_txt_to_json_converter(input_file, output_file):
    with open(input_file, 'r') as txt_file:
        lines = txt_file.readlines()

    json_data = {
        "name": lines[0].strip(),
        "line1": lines[1].strip(),
        "line2": lines[2].strip()
    }

    with open(output_file, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)

# only handles txt files given this txt format...
# SOSO-4
# 1 00004U          23274.66666667  .00000000  00000-0  00000-0 0 00004
# 2 00004 097.4153 167.6514 0009339 322.4652 253.5376 15.20925382000012

# Example usage:
#input_txt_file = 'SOSO-1_TLE.txt'  
#output_json_file = 'SOSO-1_TLE.json'  
#txt_to_json_converter(SOSO-1_TLE.txt, SOSO-1_TLE.json)