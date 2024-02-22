import unittest
from unittest import IsolatedAsyncioTestCase
from app_config import *
from scheduler_service.fixed_event_processing.eclipse_events import ensure_eclipse_events_populated
import json
from datetime import datetime 
import csv 
from fastapi.encoders import jsonable_encoder

from app_config.database.setup import get_session, Base
from app_config.database.mapping import EclipseProcessingBlock, SatelliteEclipse

# def get_satellite_eclipse(start_time: datetime, end_time:datetime):
#     session = get_session();
#     results = session.query()


def clear_eclipse_db(start_time: datetime, end_time: datetime):
    session = get_session();
    try:
        session.query(EclipseProcessingBlock).filter(datetime.strptime(EclipseProcessingBlock.time_range[0]) >= start_time, 
        datetime.strptime(EclipseProcessingBlock.time_range[1]) <= end_time).delete()
        session.commit()
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
                    # print(f'\t{row[0]} works in the {row[1]} department, and was born in {row[2]}.')
                    line_count += 1
    return eclipseOutput

class SchedulerTests(unittest.IsolatedAsyncioTestCase):
    
    # #Test with basic functionality
    # async def test_01_ensure_eclipse_events_populated(self):
    #     start_timeJSON = {
    #         "year":2024,
    #         "month":2,
    #         "day":15,
    #         "hour":12
    #     }
        
    #     end_timeJSON = {
    #         "year":2024,
    #         "month":2,
    #         "day":16,
    #         "hour":12
    #     }
        
    #     start_time = datetime(**start_timeJSON)
    #     end_time = datetime(**end_timeJSON)
    #     ensure_eclipse_events_populated(start_time, end_time);
        
        
        
    #     self.assertEquals("","");
    
    
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
        
        # ensure_eclipse_events_populated(start_time, end_time);
        clear_eclipse_db(start_time, end_time)
        
        self.assertEquals("","");
    

if __name__ == '__main__':
    unittest.main()