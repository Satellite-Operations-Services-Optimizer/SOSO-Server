import unittest
from unittest import IsolatedAsyncioTestCase
from app_config import *
from app_config.database.setup import get_session, Base
from app_config.database.mapping import ImageOrder
from image_management_service.services.handler import handle_image_orders
import json

def remove_image_order_from_db(key):
    session = get_session()
    try:
        session.query(ImageOrder).filter_by(id=key).delete()
        session.commit()
        print("Successfully removed test image order")
    
    except Exception as e:
        print(f"An error occurred removing test row: {e}")
        session.rollback()
        return None
    
    finally:
        session.close()


class TestImageManagementService(unittest.IsolatedAsyncioTestCase):
    
    #Valid input with reccurrence
    async def test_01_handle_image_orders(self):
        imageRequestJSON = '{"Latitude": 37.348835836258075,"Longitude": 47.714415386670055,"Priority": 1,"ImageType": "Medium","ImageStartTime": "2023-11-18T05:30:22","ImageEndTime": "2023-11-18T19:34:28","DeliveryTime": "2023-11-19T03:34:28","Recurrence": {"Revisit": "True","NumberOfRevisits": 3,"RevisitFrequency": 6,"RevisitFrequencyUnits": "Days"}}'
        
        sampleImgReq = json.loads(imageRequestJSON);
        
        returnable, key = handle_image_orders(sampleImgReq)
        
        print("output: ", returnable)
        
        expected = "{'latitude': 37.348835836258075, 'longitude': 47.714415386670055, 'priority': 1, 'image_type': 'Medium', 'window_start': '2023-11-18T05:30:22', 'window_end': '2023-11-18T19:34:28', 'delivery_deadline': '2023-11-19T03:34:28', 'revisit_frequency': datetime.timedelta(days=6), 'number_of_visits': 4}"
        
        self.assertEquals(str(returnable), expected);
        remove_image_order_from_db(key);
    
    # Valid input without reccurence
    async def test_02_handle_image_orders(self):
        imageRequestJSON = '{"Latitude": -88.33002794624812,"Longitude": -95.14940691709423,"Priority": 3,"ImageType": "Low","ImageStartTime": "2023-11-18T04:55:36","ImageEndTime": "2023-11-18T07:57:21","DeliveryTime": "2023-11-18T15:57:21","Recurrence": {"Revisit": "False"}}'
        
        sampleImgReq = json.loads(imageRequestJSON);
        
        returnable, key = handle_image_orders(sampleImgReq)
        
        expected = "{'latitude': -88.33002794624812, 'longitude': -95.14940691709423, 'priority': 3, 'image_type': 'Low', 'window_start': '2023-11-18T04:55:36', 'window_end': '2023-11-18T07:57:21', 'delivery_deadline': '2023-11-18T15:57:21', 'revisit_frequency': None, 'number_of_visits': 1}"
        
        self.assertEquals(str(returnable), expected);
        remove_image_order_from_db(key);
        
    # Invalid input with incorrectly formatted image request (Recurrence Missing)
    async def test_03_handle_image_orders(self):
        imageRequestJSON = '{"Latitude": -88.33002794624812,"Longitude": -95.14940691709423,"Priority": 3,"ImageType": "Low","ImageStartTime": "2023-11-18T04:55:36","ImageEndTime": "2023-11-18T07:57:21","DeliveryTime": "2023-11-18T15:57:21"}'
        
        sampleImgReq = json.loads(imageRequestJSON);
        
        returnable = handle_image_orders(sampleImgReq)
        
        expected = ("", -1)
        
        self.assertEquals(returnable, expected);
    
    # Empty input
    async def test_04_handle_image_orders(self):
        sampleImgReq = {};
        
        returnable = handle_image_orders(sampleImgReq)
        
        expected = ("", -1)
        
        self.assertEquals(returnable, expected);

if __name__ == '__main__':
    unittest.main()