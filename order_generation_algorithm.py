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
image_order_dir = "database_scripts/populate_scripts/sample_image_orders"
maintenance_order_dir = "database_scripts/populate_scripts/sample_maintenance_orders"
outage_order_dir = "database_scripts/populate_scripts/sample_outage_orders"

# Random order generation algorithm
# Image orders are generated with random data and dates
def generate_image_order(order_id, start_time, end_time):
    order = {
        "Latitude": random.uniform(-85, 85),
        "Longitude": random.uniform(-180, 180),
        "Priority": random.randint(1, 3),
        "ImageType": random.choice(["Spotlight", "Medium", "Low"]),
        "ImageStartTime": random_date(start_time, end_time).isoformat(),
        "ImageEndTime": random_date(start_time, end_time).isoformat(),
        "DeliveryTime": random_date(start_time, end_time).isoformat(),
        "Recurrence": {
            "Revisit": random.choice(["True", "False"]),
            "NumberOfRevisits": random.randint(1, 10) if random.choice([True, False]) else None,
            "RevisitFrequency": random.randint(1, 30) if random.choice([True, False]) else None,
            "RevisitFrequencyUnits": random.choice(["Days", "Hours"]) if random.choice([True, False]) else None
        }
    }
    file_name = f"Order_{order_id:02}.json"
    with open(file_name, 'w') as f:
        json.dump(order, f, indent=4)
    return file_name

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
                "MinimumGap": str(random.randint(1, 10000)) if activity != "OrbitManeuver" else "Null",
                "MaximumGap": str(random.randint(1, 10000)) if activity != "OrbitManeuver" else "Null"
            },
            "Repetition": str(random.randint(1, 50)) if activity != "OrbitManeuver" else "Null"
        },
        "PayloadOutage": random.choice(["TRUE", "FALSE"])
    }
    file_name = f"{activity}maintenance{order_id:02}.json"
    with open(file_name, 'w') as f:
        json.dump(order, f, indent=4)
    return file_name

# Outage Order Generation Algorithm
def generate_outage_order(target, start_time, end_time):
    order = {
        "Target": target,
        "Activity": "Outage",
        "Window": {
            "Start": random_date(start_time, end_time).isoformat(),
            "End": random_date(start_time, end_time).isoformat()
        }
    }
    file_name = f"{target}Outage.json"
    with open(file_name, 'w') as f:
        json.dump(order, f, indent=4)
    return file_name

# Main loop
def main(num_orders, num_satellites, start, end):
    start_time = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S")
    end_time = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S")
    
    # Change working directory to the target directories for each order type
    os.chdir(image_order_dir)
    for i in range(1, num_orders + 1):
        file_name = generate_image_order(i, start_time, end_time)
        print(f"Generated {file_name}")

    os.chdir(maintenance_order_dir)
    # Generate maintenance orders
    for i in range(1, num_orders + 1):
        maintenance_file_name = generate_maintenance_order(i, "maintenance", num_satellites, start_time, end_time)
        print(f"Generated {maintenance_file_name}")

    os.chdir(outage_order_dir)
    # Generate outage orders for each satellite
    for j in range(1, num_satellites + 1):
        outage_file_name = generate_outage_order(f"SOSO-{j}", start_time, end_time)
        print(f"Generated {outage_file_name}")

    # Git operations (within each target directory)
    for directory in [image_order_dir, maintenance_order_dir, outage_order_dir]:
        os.chdir(directory)
        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'commit', '-m', 'Add randomized orders'])
        subprocess.run(['git', 'push'])

# Execute Script
if __name__ == "__main__":
    main(num_orders=10, num_satellites=5, start="2024-03-20T00:00:00", end="2024-10-20T00:00:00")