from pydantic import BaseModel
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy import Column, DateTime, Interval, ForeignKey, INT, String, Float, BOOLEAN, DOUBLE_PRECISION, VARCHAR, TIMESTAMP
from sqlalchemy.sql import func

from sqlalchemy.orm import DeclarativeBase



func: callable
#Base  = declarative_base(
class Base(DeclarativeBase):
    pass
    __allow_unmapped__ = True
    extend_existing=True
    
class satellite_maintenance_request(Base):
    __tablename__ = 'satellite_maintnence_request'
    id= Column(INT, primary_key=True, index=True)
    activity_description= Column(VARCHAR)
    start_time= Column(TIMESTAMP)
    end_time= Column(TIMESTAMP)
    duration= Column(Interval)
    repetition= Column(Interval)
    frequency_min_gap= Column(Interval)
    frequency_max_gap= Column(Interval)
    payload_flag= Column(BOOLEAN)


# CREATE INDEX idx_time= Column(ON satellite_maintenance_request(Base):
# 	image_start_time,
# 	image_end_time


class satellite_maintenance_request_bridge(Base):
    __tablename__ = 'satellite_maintenance_request_bridge'
    satellite_id= Column(INT, primary_key=True, index=True)
    maintenance_id= Column(INT)
	# PRIMARY KEY (satellite_id, maintenance_id)
	# CONSTRAINT fk_satellite_id= Column(FOREIGN KEY (satellite_id) REFERENCES satellite(Base):id) ON UPDATE CASCADE ON DELETE CASCADE,
	# CONSTRAINT fk_maintenance_id= Column(FOREIGN KEY (maintenance_id) REFERENCES satellite_maintenance_request(Base):id) ON UPDATE CASCADE ON DELETE CASCADE


class satellite_outage_request(Base):
    __tablename__ = 'satellite_outage_request'
    id= Column(INT, primary_key=True, index=True)
    satellite_id= Column(INT)
    start_time= Column(TIMESTAMP)
    end_time= Column(TIMESTAMP)
    status= Column(INT)

class outage_activity(Base):
    __tablename__ = 'outage_activity'
    id = Column(INT, primary_key=True, index=True)
    satellite_id= Column(INT)
    start_time= Column(TIMESTAMP)
    end_time= Column(TIMESTAMP)
    status= Column(INT)
    satellite_activity_schedule_id= Column(INT)
    
    class Config:
        from_attributes = True
# CREATE INDEX idx_time= Column(ON satellite_outage_request(Base):
# 	image_start_time,
# 	image_end_time


class satellite_outage_request_bridge(Base):
    __tablename__ = 'satellite_outage_request_bridge'
    satellite_id= Column(INT, primary_key=True, index=True)
    outage_request_id= Column(INT)
	# PRIMARY KEY (satellite_id, outage_request_id)
	# CONSTRAINT fk_satellite_id= Column(FOREIGN KEY (satellite_id) REFERENCES satellite(Base):id) ON UPDATE CASCADE ON DELETE CASCADE,
	# CONSTRAINT fk_outage_request_id= Column(FOREIGN KEY (outage_request_id) REFERENCES satellite_outage_request(Base):id) ON UPDATE CASCADE ON DELETE CASCADE


class ground_station_outage_request(Base):
    __tablename__ = 'ground_station_outage_request'
    id= Column(INT, primary_key=True, index=True)
    ground_station_id= Column(INT)
    start_time= Column(TIMESTAMP)
    end_time= Column(TIMESTAMP)
    status= Column(INT)
	# CONSTRAINT fk_ground_station_id= Column(FOREIGN KEY (ground_station_id) REFERENCES ground_station(Base):id) ON UPDATE CASCADE ON DELETE CASCADE


# CREATE INDEX idx_time= Column(ON ground_station_outage_request(Base):
# 	image_start_time,
# 	image_end_time



class satellite_activity_schedule(Base):
    __tablename__ = 'satellite_activity_schedule'
    id= Column(INT, primary_key=True, index=True)
    satellite_id= Column(INT)
    start_time= Column(TIMESTAMP)
    end_time= Column(TIMESTAMP)
    image_activity_id= Column(INT)
    downlink_activity_id= Column(INT)
    maintenance_activity_id= Column(INT)
    status= Column(INT)
	# CONSTRAINT fk_satellite_id= Column(FOREIGN KEY (satellite_id) REFERENCES satellite(Base):id) ON UPDATE CASCADE ON DELETE CASCADE


class image_activity(Base):
    __tablename__ = 'image_activity'
    id= Column(INT, primary_key=True, index=True)
    image_resolution= Column(INT)
    priority= Column(INT)
    image_time= Column(TIMESTAMP)
    satellite_activity_schedule_id= Column(INT)
    # CONSTRAINT fk_satellite_activity_schedule_id= Column(FOREIGN KEY (satellite_activity_schedul_id) REFERENCES satellite_actvity_schedule(Base):id) ON UPDATE CASCADE ON DELETE CASCADE


class maintenance_activity(Base):
    __tablename__ = 'maintenance_activity'
    id= Column(INT, primary_key=True, index=True)
    description= Column(VARCHAR)
    priority= Column(INT)
    start_time= Column(TIMESTAMP)
    duration= Column(Interval)
    payload_flag= Column(BOOLEAN)
    satellite_activity_schedule_id= Column(INT)