import unittest
from unittest import IsolatedAsyncioTestCase
from app_config import *
from Models.RequestModel import *
from Services.handler import handle_image_orders

from fastapi.encoders import jsonable_encoder

class TestImageManagementService(unittest.IsolatedAsyncioTestCase):
    
    #Valid input with reccurence
    async def test_01_handle_image_orders(self):
        imageRequestJSON = '{"Latitude": 37.348835836258075,"Longitude": 47.714415386670055,"Priority": 1,"ImageType": "Medium","ImageStartTime": "2023-11-18T05:30:22","ImageEndTime": "2023-11-18T19:34:28","DeliveryTime": "2023-11-19T03:34:28","Recurrence": {"Revisit": "True","NumberOfRevisits": 3,"RevisitFrequency": 6,"RevisitFrequencyUnits": "Days"}}'
        
        sampleImgReq = ImageRequest.model_validate_json(imageRequestJSON)
        
        returnable = await handle_image_orders(sampleImgReq)
        
        comparator = ImageOrder(latitude=37.348835836258075,longitude=47.714415386670055,priority=1,image_res=2,image_height=40000,image_width=20000,start_time="2023-11-18T05:30:22",end_time="2023-11-18T19:34:28",delivery_deadline="2023-11-19T03:34:28",num_of_revisits=3,revisit_frequency=6,revisit_frequency_units="Days")
        
        self.assertEquals(jsonable_encoder(returnable), jsonable_encoder(comparator))
    
    #Valid input without reccurence
    async def test_02_handle_image_orders(self):
        imageRequestJSON = '{"Latitude": -88.33002794624812,"Longitude": -95.14940691709423,"Priority": 3,"ImageType": "Low","ImageStartTime": "2023-11-18T04:55:36","ImageEndTime": "2023-11-18T07:57:21","DeliveryTime": "2023-11-18T15:57:21","Recurrence": {"Revisit": "False"}}'
        
        sampleImgReq = ImageRequest.model_validate_json(imageRequestJSON)
        
        returnable = await handle_image_orders(sampleImgReq)
        
        comparator = ImageOrder(latitude=-88.33002794624812,longitude=-95.14940691709423,priority=3,image_res=1,image_height=40000,image_width=20000,start_time="2023-11-18T05:30:22",end_time="2023-11-18T19:34:28",delivery_deadline="2023-11-19T03:34:28",num_of_revisits=0,revisit_frequency=0,revisit_frequency_units="")
        
        self.assertEquals(jsonable_encoder(returnable), jsonable_encoder(comparator))
        
    #Invalid input with incorrectly formatted image request
    async def test_03_handle_image_orders(self):
        imageRequestJSON = '{"Latitude": -88.33002794624812,"Longitude": -95.14940691709423,"Priority": 3,"ImageType": "Low","ImageStartTime": "2023-11-18T04:55:36","ImageEndTime": "2023-11-18T07:57:21","DeliveryTime": "2023-11-18T15:57:21","Recurrence": {"Revisit": "False"}}'
        
        sampleImgReq = ImageRequest.model_validate_json(imageRequestJSON)
        
        returnable = await handle_image_orders(sampleImgReq)
        
        self.assertEqual(returnable, "")
