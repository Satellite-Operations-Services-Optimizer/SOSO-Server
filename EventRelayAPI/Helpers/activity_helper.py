from app_config.database import db_session, Base

MaintenanceOrder = Base.classes.maintenance_order

def get_all_memory_scrubs():

    try:
        memory_scrubs = db_session.query(MaintenanceOrder).filter(
            MaintenanceOrder.description == "MemoryScrub").all()
        
        return {
            "status_text": "OK",
            "status_response": 201,
            "data": memory_scrubs
        }
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: db_session.close()

def get_all_orbit_maneuvers():

    try:
        orbit_maneuvers = db_session.query(MaintenanceOrder).filter(
            MaintenanceOrder.description == "OrbitManeuver").all()
        
        return {
            "status_text": "OK",
            "status_response": 201,
            "data": orbit_maneuvers
        }
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: db_session.close()

def get_all_orbit_parameter_updates():

    try:
        orbit_parameter_update = db_session.query(MaintenanceOrder).filter(
            MaintenanceOrder.description == "OrbitParameterUpdate").all()
        
        return {
            "status_text": "OK",
            "status_response": 201,
            "data": orbit_parameter_update
        }
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: db_session.close()

def get_all_payload_diagnostics():

    try:
        payload_diagnostic_activities = db_session.query(MaintenanceOrder).filter(
            MaintenanceOrder.description == "PayloadDiagnosticActivity").all()
        
        return {
            "status_text": "OK",
            "status_response": 201,
            "data": payload_diagnostic_activities
        }
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: db_session.close()