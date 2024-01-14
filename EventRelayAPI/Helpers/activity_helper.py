from app_config.database import get_db_session, Base

MaintenanceOrder = Base.classes.maintenance_order

def get_all_memory_scrubs():
    session = get_db_session()
    try:
        memory_scrubs = session.query(MaintenanceOrder).filter(
            MaintenanceOrder.description == "MemoryScrub").all()
        
        return {
            "status_text": "OK",
            "status_response": 201,
            "data": memory_scrubs
        }
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: session.close()

def get_all_orbit_maneuvers():
    session = get_db_session()
    try:
        orbit_maneuvers = session.query(MaintenanceOrder).filter(
            MaintenanceOrder.description == "OrbitManeuver").all()
        
        return {
            "status_text": "OK",
            "status_response": 201,
            "data": orbit_maneuvers
        }
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: session.close()

def get_all_orbit_parameter_updates():
    session = get_db_session()
    try:
        orbit_parameter_update = session.query(MaintenanceOrder).filter(
            MaintenanceOrder.description == "OrbitParameterUpdate").all()
        
        return {
            "status_text": "OK",
            "status_response": 201,
            "data": orbit_parameter_update
        }
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: session.close()

def get_all_payload_diagnostics():
    session = get_db_session()
    try:
        payload_diagnostic_activities = session.query(MaintenanceOrder).filter(
            MaintenanceOrder.description == "PayloadDiagnosticActivity").all()
        
        return {
            "status_text": "OK",
            "status_response": 201,
            "data": payload_diagnostic_activities
        }
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally: session.close()