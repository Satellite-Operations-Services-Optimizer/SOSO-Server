from config.database import db_session, Base

Satellite = Base.classes.satellite
GroundStation = Base.classes.ground_station

def add_satellite(data) -> Satellite | None:
    """
    Adds a new satellite ssset to the 'satellite' table and returns the primary key of the added asset.
    :param data: A dictionary containing the data for the new asset.
    :return: The primary key of the newly added asset.
    """
    try:
        new_satellite = Satellite(**data)
        db_session.add(new_satellite)
        db_session.commit()
        db_session.refresh()
        
        print("New image order added successfully!")
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
        db_session.refresh()
        
        print("New image order added successfully!")
        return new_ground_station.id  
    
    except Exception as e:
        print(f"An error occurred: {e}")
        db_session.rollback()
        return None
    
    finally:
        db_session.close()
