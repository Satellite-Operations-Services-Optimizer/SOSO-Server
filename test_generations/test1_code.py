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
base_dir = os.path.dirname(os.path.abspath(__file__))
image_order_dir = os.path.join(base_dir, "test1_overlapping_parent_orders")

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Modified random order generation algorithm
def generate_image_order(order_id, start_time, end_time, priority, image_start_time, image_end_time):
    order = {
        "Latitude": random.uniform(-85, 85),
        "Longitude": random.uniform(-180, 180),
        "Priority": priority,
        "ImageType": random.choice(["Spotlight", "Medium", "Low"]),
        "ImageStartTime": image_start_time.isoformat(),
        "ImageEndTime": image_end_time.isoformat(),
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

# Main loop modified to generate overlapping orders
def main(num_orders, num_satellites, start, end):
    start_time = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S")
    end_time = datetime.strptime(end, "%Y-%m-%dT%H:%M:%S")
    
    ensure_directory_exists(image_order_dir)  # Ensure the directory exists
    os.chdir(image_order_dir)
    priority = random.randint(1, 3)
    image_start_time = random_date(start_time, end_time)
    image_end_time = image_start_time + timedelta(hours=random.randint(1, 3))  # Ensure overlap possibility
    
    for i in range(1, num_orders + 1):
        file_name = generate_image_order(i, start_time, end_time, priority, image_start_time, image_end_time)
        print(f"Generated {file_name}")

# Execute Script
if __name__ == "__main__":
    main(num_orders=20, num_satellites=5, start="2024-03-20T00:00:00", end="2024-10-20T00:00:00")