#!/usr/bin/env python
# coding: utf-8


import os
import json
from skyfield.sgp4lib import EarthSatellite
from skyfield.api import load, Topos
from datetime import datetime, timedelta
import math
import time
from haversine import haversine
from app_config import get_db_session
from app_config.database.mapping import GroundStation, Satellite, ImageOrder, ScheduleRequest, OutageOrder, MaintenanceOrder, ScheduledMaintenance, ScheduledOutage, ScheduledImaging, Schedule, ScheduledEvent
from sqlalchemy import case, and_, or_
from scheduler_service.constants import get_ephemeris
from scheduler_service.schedulers.utils import get_image_dimensions
from scheduler_service.event_processing.order_processing import ensure_orders_requested


start_time_str = "2023-10-08 00:00:00"
end_time_str = "2023-10-08 23:59:59"

# Convert the input strings to datetime objects
start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")




# Class to handle Ground Station operations
class ground_station:

    # Defines groun station class
    def __init__(self, name, lat, long, height, mask_receive,
                 mask_transmit, uplink_rate, downlink_rate):

        self.Name = name

        self.Latitude = lat
        self.Longitude = long
        self.Height = height

        self.StationMaskRecv = mask_receive
        self.StationMaskTrans = mask_transmit
        self.UplinkRate = uplink_rate    
        self.DownlinkRate = downlink_rate

        self.RecofigTime = 5*60
        
        self.topos = Topos(lat, long)
        
        self.availableSlots = []
        self.allocatedSlots = []
    
    # Checks to see if satellite is in contact with ground station through station mask
    def isVisibleRecv(self, sat, tm): 
        # Check if sattelite is visible from ground station for Receiving i.e. Elevation Mask
        relative_pos =  (sat.satObj - self.topos).at(tm)
        elevation_angle = relative_pos.altaz()[0]
        
        if elevation_angle.degrees > self.StationMaskRecv:
            return True
        
        return False

    # Checks to see if satellite is in contact with ground station
    def isVisibleTrans(self, sat, tm): 
        # Check if sattelite is visible from ground station for Transmitting i.e. Elevation Mask
        relative_pos =  (sat.satObj - self.topos).at(tm)
        elevation_angle = relative_pos.altaz()[0]
        
        if elevation_angle.degrees > self.StationMaskTrans:
            return True
        
        return False
    
    # Sets up slots for ground station to communicate with satellite
    def reset(self, start, end):
        # Reset the Ground Station i.e. Clear all the slots.
        slot = {}
        slot["Start"] = start
        slot["End"] = end
        
        self.availableSlots = [slot]
        self.allocatedSlots = []

    # Convert the datetime objects to skyfield Time objects
    def strToTm(self, ts, Str):        
        dt = datetime.strptime(Str, "%Y-%m-%dT%H:%M:%S")
        return ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    # Check if there is a slot available for uplink
    def canUplink(self, sched, start, ts, visibility):
        # Check if there is a slot available for uplink
        transfer_dur = len(json.dumps(sched)) / (self.UplinkRate/8)        
        delivery = self.strToTm(ts, sched['Activity Window']["Start"])
        
        return self.getSlot(start, delivery, transfer_dur, visibility)
    
    # Check if there is a slot available for downlink
    def canDownlink(self, ev, tm, ts, visibility):
        # Check if there is a slot available for downlink

        duration = ev["Ref"]['Transfer Time']
        start = ts.utc(tm.utc_datetime() + timedelta(seconds=duration))

        # Size is in bytes. Divide by 8 to convert bits to bytes
        transfer_dur = ev["Ref"]['Storage'] / (self.DownlinkRate/8)
        
        delivery = self.strToTm(ts, ev["Ref"]['DeliveryTime'])
        
        return self.getSlot(start, delivery, transfer_dur, visibility)
    
    # Check if there is a slot available for both uplink and downlink
    def getSlot(self, req_start, req_end, duration, visibility):

        # check if the request is valid
        if req_end.tt < req_start.tt +duration/(3600.0*24):
            return [False, req_start]

        # Loop over available slots to check if any one of them is feasible
        for slot in self.availableSlots:

            # Loop over the slots where sattelite is visible to ground station
            for window in visibility:

                slot_start = slot["Start"]
                slot_end = slot["End"]
                
                # Check if window and slot overlap with each other
                if req_start.tt > window["Start"].tt:
                    start = req_start
                else:
                    start = window["Start"]

                if slot_start.tt > start.tt:
                    start = slot_start
                    
                if req_end.tt < window["End"].tt:
                    end = req_end
                else:
                    end = window["End"]

                if slot_end.tt < end.tt:
                    end = slot_end
                    
                # Check if overlapping slot is wide enough to accomodate transfer of data
                if end.tt > start.tt + (duration+10)/(3600.0*24):
                    #print("Res", start.utc_strftime(), end.utc_strftime())
                    return [True, start, slot]
                
        return [False, req_start, {}]
    
    # Book time slot for downlinking data
    def bookSlot(self, ev, start, slot, ts):
        # Book a time slot on Ground station
        duration = ev["Ref"]['Storage'] / self.DownlinkRate
        
        print("bookSlot", start.utc_strftime(), slot["Start"].utc_strftime(), slot["End"].utc_strftime(), duration)
        print(slot['Start'].utc_strftime(), slot['End'].utc_strftime())

        # If after spitting the free slot, we end up with a free slot at the start 
        if start.tt > slot["Start"].tt + 5/(3600.0*24):
        
            slotA = {}
            slotA["Start"] = slot["Start"]
            slotA["End"] =   ts.utc(start.utc_datetime() + timedelta(seconds=-5))
            
            self.availableSlots.append(slotA)
            #print("Slot A", slotA['Start'].utc_strftime(), slotA['End'].utc_strftime())

        # If after spitting the free slot, we end up with a free slot at the end 
        if start.tt + (duration+5)/(3600.0*24) < slot["End"].tt:
        
            slotB = {}
            slotB["Start"] = ts.utc(slot["Start"].utc_datetime() + timedelta(seconds=duration+5))
            slotB["End"] =   slot["End"]
            
            self.availableSlots.append(slotB)
            #print("Slot B", slotB['Start'].utc_strftime(), slotB['End'].utc_strftime())

        # Add the slot for transfer event
        slotN = {}
        slotN["Start"] = start
        slotN["End"] =   ts.utc(start.utc_datetime() + timedelta(seconds=duration))
        
        #print("Slot Allocated", slotN['Start'].utc_strftime(), slotN['End'].utc_strftime())

        ev["Ref"]["Slot"] = slotN
        ev["Ref"]["Station"] = self.Name

        self.allocatedSlots.append(slotN)

        # Remove the free slot, we allocated some time from it and added the remainin above
        self.availableSlots.remove(slot)

        return slotN
        



# Define satellites using class
class satelite:

    # Define satellite parameters
    def __init__(self, tle, name):
        self.name = name
        self.loadTLE(tle)
        self.initPower()
        self.StorageCapacityMax = 40*1024*1024*1024
        self.StorageCapacity = 40*1024*1024*1024
        self.viewAngle = 30
        self.viewRatio = math.sin(self.viewAngle*math.pi/180)
        self.lat = -100000
        self.long = -100000
        self.maint = []
        self.Events = []
        self.Scheduled = []
        self.outages = []
        self.last_image_time = None  # Add a new attribute to track the last image time
        
        self.stationVisibility = {}

    # Load TLE files for satellites
    def loadTLE(self, tle):

        ts = load.timescale() # Create timescale object for TLE computation

        if type(tle)!=str:
            data = tle
        else:
            with open(tle) as f:
                data = json.load(f)

        # print(data)
        self.name = data.get('name') or self.name
        line1 = data['line1']
        line2 = data['line2']
        self.satObj = EarthSatellite(line1, line2, self.name, ts) # Create new satellite object where line 1 = tle[1], line 2 = tle[2], title = tle[0], and ts for timescale

    # Define the initialization of power sources
    def initPower(self):
        # Initialize power sources for eclipse and sunlight:
        self.P_sunlit = 500  # in Watts during Sunlight
        # 200-800 Watts for research sat.
        # 1000-1500 Watts for commercial sat.
        self.P_eclipse = self.P_sunlit * 0.4  # in Watts during Eclipse (assuming 40% of power is used)

    def update(self, tm, eph, images, ts, GroundStations):

        pos = self.satObj.at(tm).position.km  # Plain (x, y, z) coordinates at the current time (Center of Earth)
        subpnt = self.satObj.at(tm).subpoint()

        pLat = self.lat
        pLong = self.long
        
        self.lat = subpnt.latitude.degrees  # Latitude at the current time
        self.long = subpnt.longitude.degrees  # Longitude at the current time

        #print("Sattelite moved by", haversine((pLat, pLong), (self.lat, self.long)))
        
        # Get the positions of the Earth, Sun, and satellite
        earth_pos = eph['earth'].at(tm).position.km
        sun_pos = eph['sun'].at(tm).position.km

        # Calculate altitude from position data
        semi_major_axis_km = self.satObj.model.a * 6378.137  # Get the semi-major axis in kilometers
        altitude = semi_major_axis_km - 6378.137  # The altitude is the semi-major axis minus the Earth's radius

        is_sunlit = self.satObj.at(tm).is_sunlit(eph) # Check if satellite is sunlit at current time

        self.fov = self.viewRatio * altitude

        #Dec = 30.0
        Dec = 6.0

        dLat = self.lat - pLat
        dLong = self.long - pLong

        dLat = dLat / Dec
        dLong = dLong / Dec

        if abs(self.lat - pLat) < 0.00001:
            return

        if abs(self.long - pLong) < 0.00001:
            return

        if pLat == -100000:
            return

        if pLong == -100000:
            return

        Lat = pLat
        Long = pLong
        for i in range(int(Dec)):    

            if Lat < -90:
                Lat = Lat + 180
                
            if Lat > 90:
                Lat = Lat - 180

            if Long < -180:
                Long = Long + 360
                
            if Long > 180:
                Long = Long - 360

            self.process_images(images, Lat, Long, tm)
            self.process_ground_stations(tm, GroundStations)
        
            Lat = (Lat + dLat)
            Long = Long + dLong
            tm = ts.utc(tm.utc_datetime() + timedelta(seconds=60/Dec))

    def process_images(self, images, Lat, Long, tm):
        total_image_time = 0  # Initialize total image time for the current eclipse period

        for im in images:
            if self.intersect(im, Lat, Long):
                if self.last_image_time is not None:
                    # Calculate the time difference between the current image and the last image
                    time_diff = (tm - self.last_image_time).tt * 24 * 3600  # in seconds
                    total_image_time += time_diff  # Add the time difference to the total image time

                if total_image_time < 360:  # Check if the total image time is less than 6 minutes (360 seconds)
                    # Process the image
                    self.logImageStart(im, tm)
                    self.last_image_time = tm  # Update the last image time
                else:
                    # If the total image time exceeds 6 minutes, stop processing images
                    break

        return total_image_time  # Return the total image time for further evaluation

    def process_ground_stations(self, tm, stations):
        for station in stations:
            if station.Name not in self.stationVisibility:
                self.stationVisibility[station.Name] = {}
                self.stationVisibility[station.Name]["Start"] = None
                self.stationVisibility[station.Name]["slots"] = []
            
            if station.isVisibleTrans(self, tm):
                if self.stationVisibility[station.Name]["Start"] is None:
                    self.stationVisibility[station.Name]["Start"] = tm
            else:
                if self.stationVisibility[station.Name]["Start"] is not None:

                    slot = {}
                    slot["Start"] = self.stationVisibility[station.Name]["Start"]
                    slot["End"] = tm
                    
                    self.stationVisibility[station.Name]["slots"].append(slot)
                    
                    self.stationVisibility[station.Name]["Start"] = None
                     
    def intersect(self, image, Lat, Long):

        distX = haversine((image['Latitude'], Long), (Lat, Long))

        distY = haversine((Lat, image['Longitude']), (Lat, Long))

        L = 0.5*image['Length']
        W = 0.5*image['Width']

        if distX < (self.fov - L) and distY < (self.fov - W):
            return True
        else:
            return False

    def logImageStart(self, im, tm):

        if self.name not in im["Sources"]:
            im["Sources"][self.name] = {}            
            im["Sources"][self.name]["session start"] = tm
            im["Sources"][self.name]["sessions"] = []
            return

        if im["Sources"][self.name]["session start"] is None:
            im["Sources"][self.name]["session start"] = tm
            return

    def logImageEnd(self, im, tm):

        if self.name not in im["Sources"]:
            return

        if im["Sources"][self.name]["session start"] is None:
            return

        dT = tm - im["Sources"][self.name]["session start"]
        dT = dT * 24 * 3600

        if dT > im['Transfer Time']:
            im["Sources"][self.name]["sessions"].append((im["Sources"][self.name]["session start"], tm, dT))

        im["Sources"][self.name]["session start"] = None
            
    def process_images(self, images, Lat, Long, tm):

        ind = 1
        for im in images:
            if self.intersect(im, Lat, Long):
                self.logImageStart(im, tm)
            else:
                self.logImageEnd(im, tm)
                                
            ind = ind +1
            
        return

    def process_images_final(self, images, tm):
        for im in images:
            self.logImageEnd(im, tm)

    def comp_time_str(self, t1_str, t2_str):

        t1 = datetime.strptime(t1_str, "%Y-%m-%dT%H:%M:%S")
        t2 = datetime.strptime(t2_str, "%Y-%m-%dT%H:%M:%S")

        if t1 > t2:
            return 1
        
        if t1 == t2:
            return 0

        if t1 < t2:
            return 1

    def add_children(self, ev, tm):

        if ev["Type"] == "Image Order":
            pass
        elif ev["Type"] == "Maintainence":
            pass
        else:
            print("Unknown event")

    def register_event(self, tm, ev, ts):

        #print("Registered Event")

        ev_begin = tm
        ev_dur = ev["Ref"]['Transfer Time']
        ev_end = ts.utc(tm.utc_datetime() + timedelta(seconds=ev_dur))

        self.Scheduled.append((ev_begin, ev_end, ev))

        ev["Ref"]["Completed"] = True
        self.add_children(ev, tm)
        ev["Ref"]["Time Start"] = tm
        ev["Ref"]["Time End"] = ev_end
        ev["Ref"]["Sat"] = self.name
        
        self.Events.remove(ev)
        
        self.StorageCapacity = self.StorageCapacity - ev["Ref"]['Storage']

    def strToTm(self, ts, Str):        
        dt = datetime.strptime(Str, "%Y-%m-%dT%H:%M:%S")
        return ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        
    def add_maint_event(self, ts, ev0):
        
        if ev0["Ref"]["RepeatCycle"]['Repetition'] == 'Null':
            return
        
        parent = ev0
        
        dur = int(ev0["Ref"]["Duration"])
        minGap = int(ev0["Ref"]["RepeatCycle"]["Frequency"]["MinimumGap"])
        maxGap = int(ev0["Ref"]["RepeatCycle"]["Frequency"]["MaximumGap"])
        
        for i in range(ev0["Level"]+1, int(ev0["Ref"]["RepeatCycle"]["Repetition"])):

            ev = {}
            ev["Type"] = "Maintainence"
            
            ev["Start"] = ts.utc(parent["Start"].utc_datetime() + timedelta(seconds=dur+minGap))
            ev["End"] = ts.utc(parent["End"].utc_datetime() + timedelta(seconds=maxGap))
            
            ev["Ref"] = parent["Ref"]
            ev["Parent"] = parent            

            parent["Child"].append(ev)
            ev["Child"] = []
            
            ev["Level"] = i
            
            self.Events.append(ev)
            
            parent = ev

    def bifurcate_maint(self, ev, ev_begin, ev_end, ts):
        # print("Splitting ", ev["Ref"]['Activity'], "(", ev["Start"].tt, ev["End"].tt, ') by (', ev_begin.tt, ev_end.tt, ")")
        
        if (ev_begin - ev["Start"]) > int(ev["Ref"]['Duration'])/(24.0*3600.0):
            evA = {}
            evA["Type"] = "Maintainence"
            evA["Start"] = ev["Start"]
            evA["End"] = ts.utc(ev_begin.utc_datetime() - timedelta(seconds=5))
            evA["Ref"] = ev["Ref"]
            evA["Parent"] = ev["Parent"]            
            evA["Child"] = []
            evA["Level"] = ev["Level"]
            
            self.Events.append(evA)
            # print("    NodeA", evA["Start"].tt, evA["End"].tt)

            if ev["Parent"] is not None:
                ev["Parent"]["Child"].append(evA)

            self.add_maint_event(ts, evA)
            

        if (ev["End"] - ev_end) > int(ev["Ref"]['Duration'])/(24.0*3600.0):
            evB = {}
            evB["Type"] = "Maintainence"
            evB["Start"] = ts.utc(ev_end.utc_datetime() + timedelta(seconds=5))
            evB["End"] = ev["End"]
            evB["Ref"] = ev["Ref"]
            evB["Parent"] = ev["Parent"]            
            evB["Child"] = []
            evB["Level"] = ev["Level"]

            self.Events.append(evB)
            # print("    NodeB", evB["Start"].tt, evB["End"].tt)

            if ev["Parent"] is not None:
                ev["Parent"]["Child"].append(evB)

            self.add_maint_event(ts, evB)
            
                
        self.remove_maint(ev)
        
    def remove_maint(self, ev):
                
        for child in ev["Child"]:
            self.remove_maint(child)
        
        if ev["Parent"] is not None:
            ev["Parent"]["Child"].remove(ev)

        self.Events.remove(ev)
        
    def isBusy(self, ev1):
        
        if self.StorageCapacity < ev1["Ref"]['Storage']:
            return True
        
        for schedule in self.Scheduled:
            ev_begin = schedule[0]
            ev_end = schedule[1]
            
            if ev1["Start"].tt > ev_begin.tt and ev1["Start"].tt < ev_end.tt:
                return True

            if ev1["End"].tt > ev_begin.tt and ev1["End"].tt < ev_end.tt:
                return True

            if ev_begin.tt > ev1["Start"].tt and ev_begin.tt < ev1["End"].tt:
                return True

            if ev_end.tt > ev1["Start"].tt and ev_end.tt < ev1["End"].tt:
                return True

        for outage in self.outages:
            ev_begin = outage["Start"]
            ev_end = outage["End"]
            
            if ev1["Start"].tt > ev_begin.tt and ev1["Start"].tt < ev_end.tt:
                return True

            if ev1["End"].tt > ev_begin.tt and ev1["End"].tt < ev_end.tt:
                return True

            if ev_begin.tt > ev1["Start"].tt and ev_begin.tt < ev1["End"].tt:
                return True

            if ev_end.tt > ev1["Start"].tt and ev_end.tt < ev1["End"].tt:
                return True

        return False




class RLoptimizer:

    def __init__(self):
        pass
    
    def accept(self, ev):
        return True




class System:

    def __init__(self, schedule_id):
        self.schedule_id = schedule_id

        self.eph = get_ephemeris()
        self.loadGS()
        self.loadSat()
        self.loadOrders()
        self.loadMaint()

        self.ts = load.timescale() # Create timescale object for TLE computation
        self.optimizer = RLoptimizer()
        self.schedId = 0
        self.imageID = 0
        self.maintID = 0

    def loadGS(self):
        session = get_db_session()
        db_groundstations = session.query(GroundStation).all()
        self.GroundStations = [ground_station(gs.name, gs.latitude, gs.longitude, gs.elevation, gs.receive_mask, gs.send_mask, gs.uplink_rate_mbps, gs.downlink_rate_mbps) for gs in db_groundstations]
        self.groundstations_map = {gs.Name: gs for gs in self.GroundStations}

    def loadSat(self):
        session = get_db_session()
        self.Satellites = [satelite(sat.tle, sat.name) for sat in session.query(Satellite).all()]
        self.satellites_map = {sat.name: sat for sat in self.Satellites}

    def loadOutages(self):
        session = get_db_session()
        outage_orders = session.query(
            OutageOrder.asset_id,
            OutageOrder.asset_type,
            case(
                (OutageOrder.asset_type == "satellite", Satellite.name),
                (OutageOrder.asset_type == "groundstation", GroundStation.name)
            ).label("asset_name"),
            ScheduleRequest.window_start,
            ScheduleRequest.window_end,
            ScheduleRequest.duration,
            ScheduleRequest.delivery_deadline,
            ScheduleRequest.uplink_size,
            ScheduleRequest.downlink_size,
            ScheduleRequest.priority,
            ScheduleRequest.id.label("request_id")
        ).join(
            OutageOrder,
            and_(
                OutageOrder.id==ScheduleRequest.order_id,
                ScheduleRequest.order_type=="outage"
            )
        ).join(
            Satellite, Satellite.id==OutageOrder.asset_id
        ).join(
            GroundStation, GroundStation.id==OutageOrder.asset_id
        ).filter(OutageOrder.schedule_id==self.schedule_id).all()

        for outage in outage_orders:
            self.unscheduleRequest(outage.request_id, ScheduledOutage)
            outage_dict = {
                "Target": outage.asset_name,
                "Activity": "Outage",
                "Window": {
                    "Start": outage.window_start.strftime("%Y-%m-%dT%H:%M:%S"),
                    "End": outage.window_end.strftime("%Y-%m-%dT%H:%M:%S"),
                }
            }
            if outage.asset_type=="satellite" and outage.asset_name in self.satellites_map:
                self.satellites_map[outage.asset_name].outages.append(outage_dict)
            elif outage.asset_type=="groundstation" and outage.asset_name in self.groundstations_map:
                pass # need to handle groundstation outages too

    def loadOrders(self):
        session = get_db_session()
        image_orders = session.query(
            ImageOrder.latitude,
            ImageOrder.longitude,
            ImageOrder.image_type,
            ScheduleRequest.id.label("request_id"),
            ScheduleRequest.window_start,
            ScheduleRequest.window_end,
            ScheduleRequest.duration,
            ScheduleRequest.delivery_deadline,
            ScheduleRequest.uplink_size,
            ScheduleRequest.downlink_size,
            ScheduleRequest.priority
        ).join(
            ImageOrder, 
            and_(
                ScheduleRequest.order_type=="imaging",
                ScheduleRequest.order_id==ImageOrder.id
            )
        ).filter(ImageOrder.schedule_id==self.schedule_id).all()

        self.orders = []
        for index, order in enumerate(image_orders):
            length, width = get_image_dimensions(order.image_type)
            self.unscheduleRequest(order.request_id, ScheduledImaging)
            self.orders.append({
                "Latitude": order.latitude,
                "Longitude": order.longitude,
                "Priority": order.priority,
                "ImageType": order.image_type.capitalize(),
                "ImageStartTime": order.window_start.strftime("%Y-%m-%dT%H:%M:%S"),
                "ImageEndTime": order.window_end.strftime("%Y-%m-%dT%H:%M:%S"),
                "DeliveryTime": order.delivery_deadline.strftime("%Y-%m-%dT%H:%M:%S"),
                "Length": length,
                "Width": width,
                "Transfer Time": order.duration.seconds,
                "Storage": order.downlink_size*1024*1024,
                "Completed": False,
                "Sources": {},
                "Schedule": None,
                "Index": index,
                "RequestID": order.request_id # we need this to know what tables in the database are associated with which produced schedule event, so we can update the database based on the output of your schedule
            })
        self.orders = sorted(self.orders, key=lambda d: d['Priority']) 

    def loadMaint(self):
        session = get_db_session()
        image_orders = session.query(
            Satellite.name.label("asset_name"),
            MaintenanceOrder.asset_id,
            MaintenanceOrder.description,
            ScheduleRequest.window_start,
            ScheduleRequest.window_end,
            ScheduleRequest.duration,
            ScheduleRequest.delivery_deadline,
            ScheduleRequest.uplink_size,
            ScheduleRequest.downlink_size,
            ScheduleRequest.priority,
            ScheduleRequest.id.label("request_id")
        ).join(
            MaintenanceOrder,
            and_(
                ScheduleRequest.order_type=="maintenance",
                ScheduleRequest.order_id==MaintenanceOrder.id
            )
        ).join(
            Satellite, Satellite.id==MaintenanceOrder.asset_id
        ).filter(MaintenanceOrder.schedule_id==self.schedule_id).all()

        for maintenance in image_orders:
            self.unscheduleRequest(maintenance.request_id, ScheduledMaintenance)
            maintenance_order_dict = {
                "Target": maintenance.asset_name,
                "Activity": maintenance.description,
                "Window": {
                    "Start": order.window_start.strftime("%Y-%m-%dT%H:%M:%S"),
                    "End": order.window_end.strftime("%Y-%m-%dT%H:%M:%S"),
                },
                "Duration": order.duration.seconds,
                "RepeatCycle": {
                    "Frequency": {
                        "MinimumGap": 1,
                        "MaximumGap": 1
                    },
                    "Repetition": 0 # Repeats are handled by another part of the system. You are only provided with individual ScheduleRequests
                },
                "PayloadOutage": "TRUE",
                "RequestID": order.request_id # we need this to know what tables in the database are associated with which produced schedule event, so we can update the database based on the output of your schedule
            }
            if maintenance.asset_name in self.satellites_map:
                self.satellites_map[maintenance.asset_name].maint.append(maintenance_order_dict)
    
    def unscheduleRequest(self, request_id):
        session = get_db_session()
        session.query(ScheduledEvent).filter_by(request_id=request_id).delete()

        request = session.query(ScheduleRequest).filter_by(id=request_id).first()
        request.status = "received"
        
        session.commit()

        
    
    def canDownlink(self, ev, tm, sat):
        for station in self.GroundStations:
            res = station.canDownlink(ev, tm, self.ts, sat.stationVisibility[station.Name]["slots"])
            
            if res[0]:
                res.append(station)
                return res
        
        print("Can not uplink at time", tm.utc_strftime())
        return [False, tm, {}, None]
        
    def simulate(self, start, end):
        
        # Convert the datetime objects to skyfield Time objects
        self.start_sky = self.ts.utc(start.year, start.month, start.day, start.hour, start.minute, start.second)
        self.end_sky = self.ts.utc(end.year, end.month, end.day, end.hour, end.minute, end.second)
        
        minTime = self.strToTm(self.orders[0]['ImageStartTime'])
        maxTime = self.strToTm(self.orders[0]['ImageEndTime'])

        for order in sys.orders:

            if minTime.tt > self.strToTm(order['ImageStartTime']).tt:
                minTime = self.strToTm(order['ImageStartTime'])


            if maxTime.tt < self.strToTm(order['ImageEndTime']).tt:
                maxTime = self.strToTm(order['ImageEndTime'])

            if maxTime.tt < self.strToTm(order['DeliveryTime']).tt:
                maxTime = self.strToTm(order['DeliveryTime'])
                
        self.start_sky = minTime
        self.end_sky = maxTime

        tm = self.start_sky
        while tm.tt < self.end_sky.tt:  # Compare Julian dates

            for sat in self.Satellites:
                sat.update(tm, self.eph, self.orders, self.ts, self.GroundStations)

            tm = self.ts.utc(tm.utc_datetime() + timedelta(seconds=60)) # Print all variables every minute from start and end times.

        for sat in self.Satellites:
            sat.process_images_final(self.orders, self.end_sky)

    def strToTm(self, Str):        
        dt = datetime.strptime(Str, "%Y-%m-%dT%H:%M:%S")
        return self.ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        

    def run(self, start, end):

        t1 = time.time()
        self.simulate(start, end)
        t2 = time.time()

        print("Simulation took", (t2-t1)/60, "minuites")
        
        self.initOptimization()
        self.optimize()
        self.satelliteActivitySchedule()
        return self.activitySchedules

    def ev_overlap(self, ev1, ev_begin, ev_end):        
        
        if ev1["Start"].tt > ev_begin.tt and ev1["Start"].tt < ev_end.tt:
            return True

        if ev1["End"].tt > ev_begin.tt and ev1["End"].tt < ev_end.tt:
            return True

        if ev_begin.tt > ev1["Start"].tt and ev_begin.tt < ev1["End"].tt:
            return True

        if ev_end.tt > ev1["Start"].tt and ev_end.tt < ev1["End"].tt:
            return True

        return False

    def bifurcate_maint_valid(self, ev, ev_begin, ev_end):
        
        if (ev_begin - ev["Start"]) > (int(ev["Ref"]['Duration']) + 5)/(24.0*3600.0):
            return True

        if (ev["End"] - ev_end) > (int(ev["Ref"]['Duration']) + 5)/(24.0*3600.0):
            return True

        print(ev_begin.tt, ev_end.tt)
        print(ev["Start"].tt, ev["End"].tt)
        
        return False

    def proc_image_event(self, ev, tm, sat):
        
        ev_begin = tm
        ev_dur = ev["Ref"]['Transfer Time']
        ev_end = self.ts.utc(tm.utc_datetime() + timedelta(seconds=ev_dur))
        
        valid = True
        overlap = False
        for maint in sat.maint:
            
            level = 0

            survive = False
            intersect=False
            for evM in sat.Events:
                if evM["Type"] != "Maintainence":
                    continue

                if evM["Ref"] != maint:
                    continue

                if int(evM["Level"]) != level:
                    continue

                if not self.ev_overlap(evM, ev_begin, ev_end):
                    continue

                #print("Overlap Order", evM["Level"], level)
                overlap = True
                intersect = True
                if self.bifurcate_maint_valid(evM, ev_begin, ev_end):
                    #print("Survive")
                    survive = True

            if intersect:
                if not survive:
                    valid = False
            
            if maint["RepeatCycle"]['Repetition'] != 'Null':
                for level in range(1, int(maint["RepeatCycle"]["Repetition"])):
                    
                    survive = False
                    intersect=False
                    for evM in sat.Events:
                        if evM["Type"] != "Maintainence":
                            continue

                        if evM["Ref"] != maint:
                            continue
                        
                        if int(evM["Level"]) != level:
                            continue
                            
                        if not self.ev_overlap(evM, ev_begin, ev_end):
                            continue

                        # print("Overlap Order", evM["Level"], level)
                        overlap = True
                        intersect = True
                        
                        if self.bifurcate_maint_valid(evM, ev_begin, ev_end):
                            #print("Survive")
                            survive = True
                            
                    if intersect:
                        if not survive:
                            valid = False

        return valid, overlap 
    
    def initOptimization(self):
        for sat in self.Satellites:
            for maintItem in sat.maint:
                # print(maintItem)
                ev = {}
                ev["Type"] = "Maintainence"
                ev["Start"] = self.strToTm(maintItem['Window']["Start"])
                ev["End"] = self.strToTm(maintItem['Window']["End"])
                ev["Ref"] = maintItem
                ev["Parent"] = None
                ev["Child"] = []
                ev["Level"] = 0
                
                sat.Events.append(ev)
                sat.add_maint_event(self.ts, ev)
                # print(ev["Start"], ev["End"])
        
            for order in self.orders:
                start = self.strToTm(order["ImageStartTime"])
                end = self.strToTm(order["ImageEndTime"])
                
                #print(start, end)
                #print("-----------------------")
                
                if sat.name in order['Sources'].keys():
                    for session in order['Sources'][sat.name]['sessions']:
                        #print(session)
                        if session[0].tt > start.tt and session[1].tt < end.tt:
                            ev = {}
                            ev["Type"] = "Image Order"
                            ev["Start"] = session[0]
                            ev["End"] = session[1]
                            ev["Ref"] = order

                            sat.Events.append(ev)
                            #print(ev["Start"], ev["End"])

        for station in self.GroundStations:                            
            station.reset(self.start_sky, self.end_sky)
                        
    def optimize(self):

        t1 = time.time()
        tm = self.start_sky
        while tm.tt < self.end_sky.tt:  # Compare Julian dates
            

            for order in self.orders:
                consumed = False
                for sat in self.Satellites:

                    if sat.name not in order['Sources'].keys():
                        continue
                        
                    for ev in sat.Events:
                        if (tm - ev["Start"]) < 0 or (tm - ev["End"]) > 0:
                            continue
                        
                        if ev["Type"] != "Image Order":
                            continue

                        if ev["Ref"] != order:
                            continue
                            
                        if sat.isBusy(ev):
                            continue

                        valid, overlap = self.proc_image_event(ev, tm, sat)

                        if not valid:
                            continue
                            
                        res, start, slot, station = self.canDownlink(ev, tm, sat)
                        if not res:
                            continue

                        if not self.optimizer.accept(ev):
                            continue
                            
                        station.bookSlot(ev, start, slot, self.ts)

                        sat.register_event(tm, ev, self.ts)

                        if overlap:
                            
                            ev_begin = tm
                            ev_dur = ev["Ref"]['Transfer Time']
                            ev_end = self.ts.utc(tm.utc_datetime() + timedelta(seconds=ev_dur))
                            
                            bfList = []
                            for evM in sat.Events:
                                if evM["Type"] == "Maintainence":
                                    if self.ev_overlap(evM, ev_begin, ev_end):
                                        bfList.append(evM)
                                        
                            for evM in bfList:                                
                                if evM in sat.Events:
                                    sat.bifurcate_maint(evM, ev_begin, ev_end, self.ts)
                                else:                                    
                                    validBif = False
                                    for evP in bfList:                                        
                                        if evP["Ref"] == evM["Ref"]:
                                            
                                            evT = evM
                                            while evT['Parent'] is not None:                                            
                                                if evP == evT['Parent']:
                                                    validBif = True
                                                    break

                                                evT = evT['Parent']
                                                
                                    if not validBif:
                                        print("Possible corruption")

                        consumed = True
                        break

                    if consumed:
                        break

                if not consumed:
                    continue

                for sat in self.Satellites:

                    if sat.name not in order['Sources'].keys():
                        continue

                    evList = []
                    for ev in sat.Events:
                        if ev["Type"] != "Image Order":
                            continue

                        if ev["Ref"] != order:
                            continue

                        evList.append(ev)

                    for ev in evList:
                        sat.Events.remove(ev)
            
            tm = self.ts.utc(tm.utc_datetime() + timedelta(seconds=60)) # Print all variables every minute from start and end times.

        t2 = time.time()
        print("Optimization took", (t2-t1)/60, "minuites")

    def satelliteActivitySchedule(self):

        self.activitySchedules = []

        for sat in sys.Satellites:

            sched = {}
            sched["Satellite Name"] = sat.name
            sched["Schedule ID"] = self.schedId

            sched['Activity Window'] = {}
            sched['Activity Window']["Start"] = None
            sched['Activity Window']["End"] = None

            sched['Image Activities'] = []
            sched['Maintenance Activities'] = []
            sched['Downlink Activities'] = []

            for im in sat.Scheduled:

                if sched['Activity Window']["Start"] == None:
                    sched['Activity Window']["Start"] = im[0]
                elif sched['Activity Window']["Start"].tt > im[0].tt:
                    sched['Activity Window']["Start"] = im[0]

                if sched['Activity Window']["End"] == None:
                    sched['Activity Window']["End"] = im[2]['Ref']['Slot']['End']
                elif im[2]['Ref']['Slot']['End'].tt > sched['Activity Window']["End"].tt:
                    sched['Activity Window']["End"] = im[2]['Ref']['Slot']['End']

                imActivity = {}
                imActivity['Image ID'] = self.imageID
                imActivity['Type'] = im[2]['Ref']['ImageType']
                imActivity['Priority'] = im[2]['Ref']['Priority']
                imActivity['RequestID'] = im[2]['Ref']['RequestID']
                imActivity['Image Time'] = im[0].utc_strftime("%Y-%m-%dT%H:%M:%S")

                sched['Image Activities'].append(imActivity)

                dnActivity = {}
                dnActivity['Image ID'] = self.imageID
                dnActivity['Downlink Start'] = im[2]['Ref']['Slot']['Start'].utc_strftime("%Y-%m-%dT%H:%M:%S")
                dnActivity['Downlink Stop'] = im[2]['Ref']['Slot']['End'].utc_strftime("%Y-%m-%dT%H:%M:%S")
                dnActivity['Station'] = im[2]['Ref']['Station']
                sched['Downlink Activities'].append(dnActivity)

                self.imageID = self.imageID + 1

            for maintItem in sat.maint:
                for evM in sat.Events:
                    if evM["Type"] != "Maintainence":
                        continue

                    if evM["Ref"] != maintItem:
                        continue

                    if int(evM["Level"]) != 0:
                        continue

                    event = evM
                    break

                mtActivity = {}
                mtActivity['Activity ID'] = self.maintID
                mtActivity['Description'] = event['Ref']['Activity']
                mtActivity['Activity Time'] = event['Start'].utc_strftime("%Y-%m-%dT%H:%M:%S")
                mtActivity['Payload Flag'] = event['Ref']['PayloadOutage']
                mtActivity['Duration'] = event['Ref']['Duration']
                mtActivity['RequestID'] = event['Ref']['RequestID']
                sched['Maintenance Activities'].append(mtActivity)

                self.maintID = self.maintID + 1

                while len(event['Child']) > 0:
                    event = event['Child'][0]

                    mtActivity = {}
                    mtActivity['Activity ID'] = self.maintID
                    mtActivity['Description'] = event['Ref']['Activity']
                    mtActivity['Activity Time'] = event['Start'].utc_strftime("%Y-%m-%dT%H:%M:%S")
                    mtActivity['Payload Flag'] = event['Ref']['PayloadOutage']
                    mtActivity['Duration'] = event['Ref']['Duration']
                    mtActivity['RequestID'] = event['Ref']['RequestID']
                    sched['Maintenance Activities'].append(mtActivity)

                    self.maintID = self.maintID + 1


            sched['Activity Window']["Start"] = sched['Activity Window']["Start"].utc_strftime("%Y-%m-%dT%H:%M:%S")
            sched['Activity Window']["End"] = sched['Activity Window']["End"].utc_strftime("%Y-%m-%dT%H:%M:%S")

            #print()
            #print()
            #print()
            print(json.dumps(sched, indent=4))
            self.activitySchedules.append(sched)
            self.schedId = self.schedId + 1


session = get_db_session()

# Process all the orders into schedule requests
ensure_orders_requested()

default_schedule_id = int(os.getenv("DEFAULT_SCHEDULE_ID"))
sys = System(schedule_id=default_schedule_id)
schedule = sys.run(start_time, end_time)
print(schedule)


def genGroundStationRequest(self):
    for activity in self.activitySchedules:
        
        for sat in sys.Satellites:
            if sat.name == activity['Satellite Name']:
                break
                
        for station in sys.GroundStations:
            res, start, slot = station.canUplink(activity, self.start_sky, self.ts, sat.stationVisibility[station.Name]["slots"])
            
            if res:
                ev = {}
                ev["Ref"] = {}
                ev["Ref"]['Storage'] = len(json.dumps(activity))
                #station.bookSlot(ev, start, slot, self.ts)
                                
                gsRequest = {}
                gsRequest['Station Name'] = station.Name
                gsRequest['Satellite'] = sat.name
                gsRequest['Acquisition of Signal'] = None
                gsRequest['Loss of Signal'] = None
                
                for slot in sat.stationVisibility[station.Name]["slots"]:
                    if start.tt >= slot["Start"].tt and start.tt <= slot["End"].tt:
                        gsRequest['Acquisition of Signal'] = slot['Start'].utc_strftime("%Y-%m-%dT%H:%M:%S")
                        gsRequest['Loss of Signal'] = slot['End'].utc_strftime("%Y-%m-%dT%H:%M:%S")

                
                gsRequest['Satellite Schedule ID'] = activity["Schedule ID"]
                gsRequest['Images to be Downlinked'] = []
                
                print(gsRequest)
                
                break
            
            
genGroundStationRequest(sys)




for sat in sys.Satellites:
    for ev in sat.Events:
        if ev["Type"] == "Image Order":        
            print(ev["Type"])




print("Image Capture Scedule:")
print()
print("Sat      Start Time                End Time                  Type         Latitude          Longitude         Priority")
print("________________________________________________________________________________________________________________________")
for order in sys.orders:
    if order["Completed"]:
        
        print(order["Sat"], end = " | ")
        print(order["Time Start"].utc_strftime(), end = " | ")
        print(order["Time End"].utc_strftime(), end = " | ")
        print('{0: <10}'.format(order['ImageType']), end = " | ")
        print('{0:15.10f}'.format(order['Latitude']), end = " | ")
        print('{0:15.10f}'.format(order['Longitude']), end = " | ")
        print('{0: <8}'.format(order['Priority']), end = "  ")

        print()
        
print()
print()
print("Image Downlink Scedule:")
print()
print("Sat      Latitude          Longitude         Ground Station               Delivery Start            Delivery End")
print("________________________________________________________________________________________________________________________")
for order in sys.orders:
    if order["Completed"]:
        
        print(order["Sat"], end = " | ")
        print('{0:14.9f}'.format(order['Latitude']), end = " | ")
        print('{0:14.9f}'.format(order['Longitude']), end = " | ")
        print('{0: <28}'.format(order['Station']), end = " | ")
        print(order["Slot"]["Start"].utc_strftime(), end = " | ")
        print(order["Slot"]["End"].utc_strftime(), end = "")

        print()





for sat in sys.Satellites:
    
    print()
    print()
    print("Sattelite:", sat.name)
    print()
    print("Activity                    Repetitions   Iteration   Start Time                End Time")
    print("________________________________________________________________________________________________________")
    for maintItem in sat.maint:
        #print(maintItem)
        #break
        
        print('{0: <25}'.format(maintItem['Activity']), end=' | ')
        
        print('{0: <11}'.format(maintItem["RepeatCycle"]['Repetition']), end = " | ")
        
        for evM in sat.Events:
            if evM["Type"] != "Maintainence":
                continue

            if evM["Ref"] != maintItem:
                continue

            if int(evM["Level"]) != 0:
                continue

            event = evM

        ev_end = sys.ts.utc(event["Start"].utc_datetime() + timedelta(seconds=int(event["Ref"]["Duration"])))
            
        print('{0: <9}'.format(str(event["Level"])), end = " | " )
        print(event["Start"].utc_strftime(), end = " | ")
        print(ev_end.utc_strftime(), end = "  ")
        
        print()

                
        while len(event['Child']) > 0:
            event = event['Child'][0]

            ev_end = sys.ts.utc(event["Start"].utc_datetime() + timedelta(seconds=int(event["Ref"]["Duration"])))
            print("                          |             |", '{0: <9}'.format(str(event["Level"])), end = " | " )
            print(event["Start"].utc_strftime(), end = " | ")
            print(ev_end.utc_strftime(), end = "  ")

            print()
        print()




print()
print()
print("Storage Usage:")
print()
print("Sattelite      Storage Left")
print("__________________________")
for sat in sys.Satellites:
    
    print(sat.name, "     ", end = " | ")
    
    print(sat.StorageCapacity/(1024.0*1024.0*1024.0), "GB")






print()
print()
print("Ground Station Utilization")
print()

for station in sys.GroundStations:

    print()
    print()
    print(station.Name)

    print()
    print("Allocated Slots")
    print("Start                       End")
    print("____________________________________________________")
    for slot in station.allocatedSlots:
        print(slot["Start"].utc_strftime(), " | ", slot["End"].utc_strftime())
    
    
    print()
    print("Available Slots")
    print("Start                       End")
    print("____________________________________________________")
    for slot in station.availableSlots:
        print(slot["Start"].utc_strftime(), "   ", slot["End"].utc_strftime())
        
    




print()
print()
print("Ground Station Visibility")
print()

for sat in sys.Satellites:
    print(sat.name)
    for station in sat.stationVisibility:
        print()
        print("    ", station)
        print("        ", "Start                       End")
        print("        ", "____________________________________________________")
        for slot in sat.stationVisibility[station]["slots"]:
            print("        ", slot["Start"].utc_strftime(), "   ", slot["End"].utc_strftime())











