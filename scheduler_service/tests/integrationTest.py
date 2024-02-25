import unittest
from unittest import IsolatedAsyncioTestCase
from app_config import *
from scheduler_service.event_processing.eclipse_events import ensure_eclipse_events_populated
import json
from datetime import datetime 
import csv 
from fastapi.encoders import jsonable_encoder

from app_config.database.setup import get_session, Base
from app_config.database.mapping import EclipseProcessingBlock, SatelliteEclipse

async def get_satellite_eclipse(start_time: datetime, end_time:datetime):
    session = get_session()
    results = session.query(SatelliteEclipse).filter(SatelliteEclipse.start_time < end_time, SatelliteEclipse.start_time >= start_time).all()
    session.close()
    return results


def clear_eclipse_db(start_time: datetime, end_time: datetime):
    session = get_session();
    try:
        session.query(SatelliteEclipse).filter(SatelliteEclipse.start_time < end_time, SatelliteEclipse.start_time >= start_time).delete()
        
        session.commit()
        
        session.close()
    except Exception as e:
        print(f"An error occurred clearing rows: {e}")
        session.rollback()
        return None


def read_eclipse_file():
    eclipseOutput = {}
    for i in range(1,6):
        currentFile = f'SOSO-{i}_0000{i}_Eclipse_Times.csv'
        with open(f"../tests/expected_outputs/Eclipse Opportunities/{currentFile}", "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                else:
                    if i not in eclipseOutput:
                        eclipseOutput[i] = {}
                    
                    dateFormat = "%d %b %Y %H:%M:%S"
                    try:
                        startdate = row[0].split(".")[0]
                        startdate = datetime.strptime(startdate, dateFormat)
                        enddate = row[1].split(".")[0]
                        enddate = datetime.strptime(enddate, dateFormat)
                        
                        eclipseOutput[i][startdate] = enddate
                    except Exception:
                        print(f"Failed at line {line_count}")  
                    line_count += 1
    return eclipseOutput

class SchedulerTests(unittest.IsolatedAsyncioTestCase):    
    
    #Test with valid input. Input being a 12 hour period. 
    async def test_01_ensure_eclipse_events_populated(self):
        
        start_timeJSON = {
            "year":2024,
            "month":2,
            "day":15,
            "hour":12
        }
        end_timeJSON = {
            "year":2024,
            "month":2,
            "day":16,
            "hour":12
        }
        
        start_time = datetime(**start_timeJSON)
        end_time = datetime(**end_timeJSON)
        
        ensure_eclipse_events_populated(start_time, end_time);
        
        expected = read_eclipse_file();
        actual = await get_satellite_eclipse(start_time, end_time);
        clear_eclipse_db(start_time, end_time)
        
        for i in range(len(actual)):
            currStart = actual[i].start_time.replace(tzinfo=None)
            if currStart:
                currSat = actual[i].asset_id

                cond = False
                for actualStart in expected[currSat].keys():
                    diff = abs(actualStart-currStart)
                    if diff.total_seconds() <= 350:
                        print(f"{currStart} and {actualStart} passed")
                        cond = True
                        break
                self.assertTrue(cond, msg=f"{currStart} has no match.");

    #Test with invalid input. Start time occurring after the end time. 
    async def test_02_ensure_eclipse_events_populated(self):
        
        start_timeJSON = {
            "year":2024,
            "month":2,
            "day":15,
            "hour":12
        }
        end_timeJSON = {
            "year":2024,
            "month":2,
            "day":16,
            "hour":12
        }
        
        start_time = datetime(**start_timeJSON)
        end_time = datetime(**end_timeJSON)
        
        ensure_eclipse_events_populated(end_time, start_time);
        
        actual = await get_satellite_eclipse(end_time, start_time);
        
        self.assertTrue(len(actual) == 0)


    #Test with invalid input. Start time and end time being the exact same. 
    async def test_03_ensure_eclipse_events_populated(self):
        start_timeJSON = {
            "year":2024,
            "month":2,
            "day":15,
            "hour":12
        }
        end_timeJSON = {
            "year":2024,
            "month":2,
            "day":15,
            "hour":12
        }
        
        start_time = datetime(**start_timeJSON)
        end_time = datetime(**end_timeJSON)
        
        ensure_eclipse_events_populated(start_time, end_time);
        
        actual = await get_satellite_eclipse(start_time, end_time);
        
        self.assertTrue(len(actual) == 0)
        
if __name__ == '__main__':
    unittest.main()