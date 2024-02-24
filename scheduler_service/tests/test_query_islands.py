from app_config import get_db_session  
from sqlalchemy import text, func, column, cast, ARRAY, select, bindparam, false
from sqlalchemy.dialects.postgresql import TSRANGE
from sqlalchemy.sql.expression import literal_column
from typing import List, Tuple
from datetime import datetime

from scheduler_service.utils import query_islands
import pytest
from datetime import datetime

def compute_islands(input_ranges: List[Tuple[datetime, datetime]]):
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

    islands = query_islands(
        source_subquery=time_ranges,
        range_column=column('time_range'),
        partition_columns=[column('partition')],
        range_constructor=func.tsrange
    ).order_by(column('time_range')).all()
    
    island_ranges = [(island.time_range.lower, island.time_range.upper) for island in islands]
    return island_ranges


# Test case 1: No input ranges
def test_no_input_ranges():
    input_ranges = []
    expected_islands = []
    islands = compute_islands(input_ranges)
    assert len(islands) == len(expected_islands)


# Test case 2: Single input range
def test_single_input_range():
    input_ranges = [(datetime(2022, 1, 1), datetime(2022, 1, 5))]
    expected_islands = [(datetime(2022, 1, 1), datetime(2022, 1, 5))]
    islands = compute_islands(input_ranges)
    assert len(islands) == len(expected_islands)
    assert islands[0] == expected_islands[0]


# Test case 3: One island overlapping input ranges
def test_overlapping_input_ranges():
    input_ranges = [
        (datetime(2022, 1, 1), datetime(2022, 1, 5)),
        (datetime(2022, 1, 3), datetime(2022, 1, 7)),
        (datetime(2022, 1, 6), datetime(2022, 1, 10))
    ]
    expected_islands = [(datetime(2022, 1, 1), datetime(2022, 1, 10))]
    islands = compute_islands(input_ranges)
    assert len(islands) == len(expected_islands)
    assert islands[0] == expected_islands[0]


# Test case 4: 3 islands, item in middle of island spans whole island and defines its end
def test_middle_spanning_island_item_input_ranges():
    input_ranges = [
        (datetime(2022, 1, 1), datetime(2022, 1, 5)),
        (datetime(2022, 1, 7), datetime(2022, 1, 10)),
        (datetime(2022, 1, 8), datetime(2022, 1, 20)),
        (datetime(2022, 1, 12), datetime(2022, 1, 15)),
        (datetime(2022, 1, 17), datetime(2022, 1, 18)),
        (datetime(2022, 1, 22), datetime(2022, 1, 25))
    ]
    expected_islands = [
        (datetime(2022, 1, 1), datetime(2022, 1, 5)),
        (datetime(2022, 1, 7), datetime(2022, 1, 20)),
        (datetime(2022, 1, 22), datetime(2022, 1, 25))
    ]
    islands = compute_islands(input_ranges)
    assert len(islands) == len(expected_islands)
    assert islands == expected_islands


test_no_input_ranges()
test_single_input_range()
test_overlapping_input_ranges()
test_middle_spanning_island_item_input_ranges()