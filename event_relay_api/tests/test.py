import unittest
from unittest import IsolatedAsyncioTestCase
from event_relay_api.routes.asset_routes import *
from event_relay_api.routes.image_routes import *
import random
from fastapi.encoders import jsonable_encoder

from app_config import *
from app_config.database.mapping import Satellite, GroundStation


class TestAssetRoutes(unittest.IsolatedAsyncioTestCase):
    async def test_01_get_all_ground_stations(self):
        returnable = await get_all_ground_stations();
        
        session = get_db_session()
        ground_stations = session.query(GroundStation).all()
        comparator = jsonable_encoder(ground_stations)
        
        
        self.assertEqual(returnable, comparator)
        
    #get_ground_station : Test using valid inputs
    async def test_01_get_ground_station_by_id(self):
        session = get_db_session()
        sampleGroundStation = GroundStation(name="walid",
                                            latitude=-88.33002794624812, 
                                            longitude=-95.14940691709423, 
                                            elevation=300.01, 
                                            receive_mask=1.1,
                                            send_mask=1.1,
                                            uplink_rate_mbps=13.1,
                                            downlink_rate_mbps=14.1)
        session.add(sampleGroundStation)
        session.commit()
        session.refresh(sampleGroundStation)
        
        comparator = session.query(GroundStation).filter_by(id=sampleGroundStation.id).first()
        
        returnable = await get_ground_station(sampleGroundStation.id)
        
        self.assertEqual(jsonable_encoder(returnable), jsonable_encoder(comparator))
        
        session.delete(sampleGroundStation)
        session.commit()
        
    #get_ground_station : Test using invalid inputs
    async def test_02_get_ground_station_by_id(self):
        session = get_db_session()
        
        randomID = 2
        while session.query(GroundStation).filter_by(id=randomID).first() is not None:
            randomID = random.randint(0,1000)
        
        with self.assertRaises(HTTPException) as e:
            await get_ground_station(randomID)
         
    #new ground_station: test using valid input
    async def test_01_new_ground_station(self):
        # EDIT THE BELOW TEST METHOD TO FIT THE GS CORRECT PARAMETERS
        newGroundStation = GroundStationCreationRequest(name="walid", latitude=19012.812, longitude=180231.1231, elevation=19.123, station_mask=123.21, uplink_rate=12.1, downlink_rate=123.21)
        
        returnableID = await new_ground_station(newGroundStation)
        
        alchemyGroundStation = GroundStation(**(newGroundStation.model_dump))
        session = get_db_session()
        result = session.query(GroundStation).filter_by(name=newGroundStation.name, latitude=newGroundStation.latitude).first()
        session.refresh(alchemyGroundStation)
        
        self.assertEqual(returnableID, result.id)
        
        session.delete(alchemyGroundStation)
        session.commit()

    #new ground_station: test using invalid input; gs with missing attributes
    async def test_02_new_ground_station(self):
        # EDIT THE BELOW TEST METHOD TO FIT THE GS CORRECT PARAMETERS
        newGroundStation = GroundStationCreationRequest(name="walid", latitude=19012.812, longitude=180231.1231, elevation=19.123, station_mask=123.21, uplink_rate=12.1, downlink_rate=123.21)
        
        with self.assertRaises(HTTPException) as e:
            await new_ground_station(newGroundStation)
            
    #new ground_station: test using invalid input; gs with wrong attributes
    async def test_03_new_ground_station(self):
        # EDIT THE BELOW TEST METHOD TO FIT THE GS CORRECT PARAMETERS
        newGroundStation = GroundStationCreationRequest(name="walid", latitude=19012.812, longitude=180231.1231, elevation=19.123, station_mask=123.21, uplink_rate=12.1, downlink_rate=123.21)
        
        with self.assertRaises(HTTPException) as e:
            await new_ground_station(newGroundStation)

    #new ground_station: test using invalid input; empty request
    async def test_04_new_ground_station(self):
        # EDIT THE BELOW TEST METHOD TO FIT THE GS CORRECT PARAMETERS
        newGroundStation = None

        with self.assertRaises(HTTPException) as e:
            await new_ground_station(newGroundStation)
   
class TestImageRoutes(unittest.IsolatedAsyncioTestCase):
    
        #create_image_order: test with valid input
        async def test_01_create_image_order(self):
            jsonData = '{"Latitude": 37.348835836258075,"Longitude": 47.714415386670055,"Priority": 1,"ImageType": "Medium","ImageStartTime": "2023-11-18T05:30:22","ImageEndTime": "2023-11-18T19:34:28","DeliveryTime": "2023-11-19T03:34:28","Recurrence": {"Revisit": "True","NumberOfRevisits": 3,"RevisitFrequency": 6,"RevisitFrequencyUnits": "Days"}}'
            
            sampleImgReq = ImageRequest.model_validate_json(jsonData)
            
            
            returnable = await handle_request(sampleImgReq)

            expected = jsonable_encoder(
                EventRelayApiMessage(
                    body=jsonable_encoder(sampleImgReq),
                    details=RequestDetails(requestType="image-order-request")
                )
            )
            
            self.assertEqual(returnable,expected)
        
        #create_image_order: test with invalid input (missing an attribute in image request)
        async def test_02_create_image_order(self):
            jsonData = '{"Latitude": 37.348835836258075,"Longitude": 47.714415386670055,"Priority": 1,"ImageType": "Medium","ImageStartTime": "2023-11-18T05:30:22","ImageEndTime": "2023-11-18T19:34:28","Recurrence": {"Revisit": "True","NumberOfRevisits": 3,"RevisitFrequency": 6,"RevisitFrequencyUnits": "Days"}}'
            
            sampleImgReq = json.loads(jsonData)
            
            with self.assertRaises(Exception) as e:
                await handle_request(sampleImgReq)
            
        #create_image_order: test with invalid input (empty param)
        async def test_03_create_image_order(self):
            
            sampleImgReq = {}
            
            with self.assertRaises(Exception) as e:
                await handle_request(sampleImgReq)    

        #get_all_image_orders: test if values are returned
        async def test_04_get_all_image_orders(self):
            returnable = await get_all_image_orders()
            
            session = get_db_session()
            
            expected = session.query(ImageOrder).all()
            
            if len(expected) > 0:
                self.assertTrue(len(returnable) > 0)
            else:
                self.assertFalse(len(returnable) > 0)
            

if __name__ == '__main__':
    unittest.main()