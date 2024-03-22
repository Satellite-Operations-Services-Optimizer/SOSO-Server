from datetime import datetime
from app_config.database.mapping import StateCheckpoint, Schedule, Satellite, AssetState
from app_config import get_db_session

def test_filtering_by_storage_capacity():
    session = get_db_session()
    schedule = Schedule(name="test filtering schedule candidates by storage capacity")
    session.add(schedule)
    session.flush()

    satellite = session.query(Satellite).first()

    starting_time = datetime(2022, 5, 15, 0, 0, 0)

    image_storage = 

    checkpoint_storage = 
    start_checkpoint = StateCheckpoint(
        schedule_id=schedule.id,
        asset_id=satellite.id,
        asset_type="satellite",
        checkpoint_time=starting_time,
        state=AssetState(
            storage=checkpoint_storage,
            storage_util=checkpoint_storage / satellite.storage_capacity,
            throughput=0,
            energy_usage=0,
            power_draw=0
        )
    )