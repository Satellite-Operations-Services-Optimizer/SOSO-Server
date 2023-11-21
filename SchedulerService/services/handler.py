from config import db_session
from Models.Satellite import Satellite, SatelliteStateGenerator
from datetime import datetime, timedelta
def handle_message(body):
    satellite = db_session.query(Satellite).first()
    state_generator = SatelliteStateGenerator(satellite)

    start_time = datetime.now()
    end_time = start_time + timedelta(days=5)
    time_delta = timedelta(seconds=1)
    for state in state_generator.track(start_time, end_time, time_delta):
        print(state)