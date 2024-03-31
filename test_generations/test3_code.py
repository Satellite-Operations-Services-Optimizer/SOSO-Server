import json
import random
import os
import subprocess
from datetime import datetime, timedelta

# Helper function to generate random data and dates
def random_date(start, end):
    """Generate a random date between `start` and `end`."""
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + timedelta(seconds=random_second)

def random_target(num_satellites):
    """Generate a random satellite target."""
    return f"SOSO-{random.randint(1, num_satellites)}"

# Directory creation and navigation
# Define the relative target directories for each order type
base_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory where the script is located
maintenance_order_dir = os.path.join(base_dir, "test3_payload_outage")

# Ensure directory exists function
def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Random order generation algorithm
# Maintenance Order Generation Algorithm
def generate_maintenance_order(order_id, order_type, num_satellites, start_time, end_time):
    activities = ["MemoryScrub", "OrbitManeuver", "OrbitParameterUpdate", "PayloadDiagnosticActivity"]
    activity = random.choice(activities)
    order = {
        "Target": random_target(num_satellites),
        "Activity": activity,
        "Window": {
            "Start": random_date(start_time, end_time).isoformat(),
            "End": random_date(start_time, end_time).isoformat()
        },
        "Duration": str(random.randint(1, 1000)),
        "RepeatCycle": {
            "Frequency": {
                "MinimumGap": str(random.randint(1, 100000)) if activity != "OrbitManeuver" else "Null",
                "MaximumGap": str(random.randint(1, 100000)) if activity != "OrbitManeuver" else "Null"
            },
            "Repetition": str(random.randint(1, 50)) if activity != "OrbitManeuver" else "Null"
        },
        "PayloadOutage": "TRUE"
    }
    file_name = f"{activity}maintenance{order_id:02}.json"
    with open(file_name, 'w') as f:
        json.dump(order, f, indent=4)
    return file_name

# Main loop
def main(num_orders, num_satellites, start, end):
    start_time = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S")
    end_time = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S")

    os.chdir(maintenance_order_dir)
    # Generate maintenance orders
    for i in range(1, num_orders + 1):
        maintenance_file_name = generate_maintenance_order(i, "maintenance", num_satellites, start_time, end_time)
        print(f"Generated {maintenance_file_name}")

# Execute Script
if __name__ == "__main__":
    main(num_orders=25, num_satellites=5, start="2024-03-20T00:00:00", end="2024-10-20T00:00:00")