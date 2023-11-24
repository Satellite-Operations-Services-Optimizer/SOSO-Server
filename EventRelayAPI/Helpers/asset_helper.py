from fastapi import HTTPException, status
from config.database import db_session, Base

Satellite = Base.classes.satellite
GroundStation = Base.classes.ground_station

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
        db_session.add(new_satellite)
        db_session.commit()
        db_session.refresh(new_satellite)
        return new_satellite.id  
    
    except Exception as e:
        print(f"An error occurred: {e}")
        db_session.rollback()
        return None
    
    finally:
        db_session.close()

def add_ground_station(data) -> GroundStation | None:
    """
    Adds a new ground station assset to the 'ground_station' table and returns the primary key of the added asset.
    :param data: A dictionary containing the data for the new asset.
    :return: The primary key of the newly added asset.
    """
    try:
        new_ground_station = GroundStation(**data)
        db_session.add(new_ground_station)
        db_session.commit()
        db_session.refresh(new_ground_station)     
        return new_ground_station.id  
    
    except Exception as e:
        print(f"An error occurred: {e}")
        db_session.rollback()
        return None
    
    finally:
        db_session.close()

def get_all_ground_stations():
    """
    Queries ground_station table to select for all rows.
    :return: a list of all rows in ground_station table
    """
    try:
        all_ground_stations = db_session.query(GroundStation).all()
        return all_ground_stations
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: db_session.close()

def get_ground_station_by_id(id):
    """
    Queries ground_station table to select for the row where param id is equivalent to ground_station.id.
    :return: the row in ground_station table with the id of input
    :exception: 404 not found if row with param id is not present
    """
    try:
        ground_station = db_session.query(GroundStation).filter(GroundStation.id==id).first()

        if not ground_station:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ground station with id {id} not found")

        return ground_station
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: db_session.close()

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