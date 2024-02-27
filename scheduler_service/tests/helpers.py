from app_config import get_db_session
from sqlalchemy import text, func, column, cast, ARRAY, select, bindparam, false
from sqlalchemy.dialects.postgresql import TSRANGE
from sqlalchemy.sql.expression import literal_column
from typing import List, Tuple
from datetime import datetime

def create_timeline_subquery(input_ranges: List[Tuple[datetime, datetime]]):
    session = get_db_session()
    if len(input_ranges)==0:
        time_ranges = session.query(
            literal_column("NULL").label("partition"),
            func.tsrange('infinity', 'infinity').label("time_range")
        ).filter(false()).subquery() # empty result set
    else:
        datetime_range_objects = [session.execute(select(func.tsrange(input_range[0], input_range[1]))).scalar() for input_range in input_ranges]
        time_ranges = session.query(
            literal_column('1').label('partition'),  # TODO:  all the same partition for now. Will test partitioning in the future
            func.unnest(datetime_range_objects).label('time_range') 
        ).subquery()
    return time_ranges