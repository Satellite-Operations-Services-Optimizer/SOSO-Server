import random
from app_config.database.mapping import image_order, ground_station, satellite, uplink_station, downlink_station, db_session
from app_config import get_db_session

## 1. Define the Particle Class:
# 

class Particle: