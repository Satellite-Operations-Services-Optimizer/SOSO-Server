from app_config.database.setup import get_session
from app_config.database.mapping import Satellite, GroundStation


def add_satellite(tle_json, tle_dict, form_data) -> Satellite | None:
    """
    Adds a new satellite ssset to the 'satellite' table and returns the primary key of the added asset.
    :param data: A dictionary containing the data for the new asset.
    :return: The primary key of the newly added asset.
    """
    new_satellite = Satellite(
                name=tle_dict["name"],
                tle=tle_json,
                storage_capacity=form_data.storage_capacity,
                power_capacity=form_data.power_capacity,
                fov_max=form_data.fov_max,
                fov_min=form_data.fov_min,
                is_illuminated=False,
                under_outage=False
            )

    try:
        #new_satellite = Satellite(tle = data, table_data)
        session = get_session()
        session.add(new_satellite)
        session.commit()
        session.refresh(new_satellite)
        return new_satellite.id  
    
    except Exception as e:
        print(f"An error occurred: {e}")
        session.rollback()
        return None
    
    finally:
        session.close()

""" def modify_ground_station_by_name(name):

    try:
        ground_station_query = db_session.query(GroundStation).filter(GroundStation.name==name)
        ground_station = ground_station_query.first()

        if ground_station == None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {name} not found")
        
        ground_station_query.update(ground_station.name)

        return 

    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: db_session.close() """