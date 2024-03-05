import unittest
from unittest import IsolatedAsyncioTestCase
from app_config import *
from scheduler_service.event_processing.eclipse_events import ensure_eclipse_events_populated
from scheduler_service.event_processing.contact_events import ensure_contact_events_populated
import json
from datetime import datetime, timedelta, UTC
import csv 
from fastapi.encoders import jsonable_encoder

from app_config.database.setup import get_session, Base
from app_config.database.mapping import EclipseProcessingBlock, SatelliteEclipse, GroundStation, ContactEvent

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



def get_gs_ids():
    returnable = {}
    
    session = get_session()
    results = session.query(GroundStation).all()
    
    for gs in results:
        returnable[gs.name] = gs.id

    session.close()
    
    return returnable
    
async def get_contacts(start_time: datetime, end_time:datetime):
    session = get_session()
    results = session.query(ContactEvent).filter(ContactEvent.start_time < end_time, ContactEvent.start_time >= start_time).all()
    session.close()
    return results

def read_contact_file(gs_ids):
    contact_output = {}
    for i in range(1,6):
        fileName = f"sat{i}.csv"
        with open(f"./expected_outputs/Contact Opportunities/{fileName}", "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            currentGS = None
            for row in csv_reader:
                if len(row) == 1:
                    currentGS = gs_ids[row[0]]
                    if currentGS not in contact_output:
                        contact_output[currentGS] = {}
                elif len(row) > 1:
                    
                    dateFormat = "%d %b %Y %H:%M:%S"
                    try:
                        startdate = row[1].split(".")[0]
                        startdate = datetime.strptime(startdate, dateFormat)
                        startdate = startdate + timedelta(hours=5)
                        enddate = row[2].split(".")[0]
                        enddate = datetime.strptime(enddate, dateFormat)
                        enddate = enddate + timedelta(hours=5)
                        
                        if i not in contact_output[currentGS]:
                            contact_output[currentGS][i] = {}
                        
                        contact_output[currentGS][i][startdate] = enddate
                        print(f'GS {currentGS} Sat {i} | {startdate} && {enddate}')
                    except Exception:
                        print(f"Failed at line {line_count}")  
                    
                line_count += 1;
    return contact_output
    
def clear_contact_db(start_time: datetime, end_time: datetime):
    session = get_session();
    try:
        session.query(ContactEvent).filter(ContactEvent.start_time < end_time, ContactEvent.start_time >= start_time).delete()
        
        session.commit()
        
        session.close()
    except Exception as e:
        print(f"An error occurred clearing rows: {e}")
        session.rollback()
        return None
    
    
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
    
    async def test_01_ensure_contact_events_populated(self):
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
        
        ensure_contact_events_populated(start_time, end_time);
        
        groundstationids = get_gs_ids()
        print("Expected Output Rows: ")
        expectedOutput = read_contact_file(groundstationids)
        
        actual = await get_contacts(start_time, end_time)
        
        print("Actual Output Rows: ")
        for row in actual:
            print(f'GS {row.groundstation_id} | SAT {row.asset_id} | {row.utc_time_range}')
        
        print("Results")
        cond = True
        for currentRow in actual:
            
            currentGS = currentRow.groundstation_id
            currentSat = currentRow.asset_id
            currentStart = currentRow.start_time.replace(tzinfo=None)
            currentStart += timedelta(hours=5)
            tempCond = False
            for expectedStart in expectedOutput[currentGS][currentSat].keys():
                diff = abs(currentStart-expectedStart)
                if diff.total_seconds() <= 600:
                    print(f'{currentStart} matches with {expectedStart} | GS: {currentGS}, SAT: {currentSat}')
                    tempCond = True
            if tempCond == False:    
                print(f'{currentStart} has no match in expected output. | GS: {currentGS}, SAT: {currentSat}')
                cond = False
        
        clear_contact_db(start_time, end_time);
        self.assertTrue(cond);
        
        
    async def test_02_ensure_contact_events_populated(self):
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
        
        ensure_contact_events_populated(end_time, start_time);
        
        actual = await get_contacts(end_time, start_time);
        
        self.assertTrue(len(actual) == 0)
        
    async def test_03_ensure_contact_events_populated(self):
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
        
        ensure_contact_events_populated(start_time, end_time);
        
        actual = await get_contacts(start_time, end_time);
        
        self.assertTrue(len(actual) == 0)
    
if __name__ == '__main__':
    unittest.main()