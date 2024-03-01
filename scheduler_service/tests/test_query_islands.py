from app_config import get_db_session  
from sqlalchemy import text, func, column, cast, ARRAY, select, bindparam, false
from sqlalchemy.dialects.postgresql import TSRANGE
from sqlalchemy.sql.expression import literal_column
from typing import List, Tuple
from datetime import datetime

from datetime import datetime
from scheduler_service.schedulers.utils import query_islands
from scheduler_service.tests.helpers import create_timeline_subquery
import itertools

def compute_islands(input_ranges: List[Tuple[datetime, datetime]]):
    timeline = create_timeline_subquery(input_ranges)
    islands = query_islands(
        source_subquery=timeline,
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

# Test case 5: Last range in island is contained within the island
def test_last_range_contained_within_island():
    input_ranges = [
        (datetime(2022, 1, 1), datetime(2022, 1, 5)),
        (datetime(2022, 1, 3), datetime(2022, 1, 20)),
        (datetime(2022, 1, 12), datetime(2022, 1, 15))
    ]
    expected_islands = [
        (datetime(2022, 1, 1), datetime(2022, 1, 20))
    ]
    islands = compute_islands(input_ranges)
    assert len(islands) == len(expected_islands)
    assert islands == expected_islands


# Test case 6: Last range in island extends the island
def test_last_range_extends_island():
    input_ranges = [
        (datetime(2022, 1, 1), datetime(2022, 1, 5)),
        (datetime(2022, 1, 7), datetime(2022, 1, 10)),
        (datetime(2022, 1, 9), datetime(2022, 1, 15))
    ]
    expected_islands = [
        (datetime(2022, 1, 1), datetime(2022, 1, 5)),
        (datetime(2022, 1, 7), datetime(2022, 1, 15))
    ]
    islands = compute_islands(input_ranges)
    assert len(islands) == len(expected_islands)
    assert islands == expected_islands

def test_permutation_invariance():
    input_ranges = [
        (datetime(2022, 5, 14, 23, 59, 37), datetime(2022, 5, 15, 0, 2, 54)),
        (datetime(2022, 5, 15, 0, 0, 0), datetime(2022, 5, 15, 0, 0, 45)),
        (datetime(2022, 5, 15, 0, 3, 39), datetime(2022, 5, 15, 0, 4, 24)),
        (datetime(2022, 5, 15, 0, 3, 49), datetime(2022, 5, 15, 0, 5, 19))
    ]
    expected_islands = [
        (datetime(2022, 5, 14, 23, 59, 37), datetime(2022, 5, 15, 0, 2, 54)),
        (datetime(2022, 5, 15, 0, 3, 39), datetime(2022, 5, 15, 0, 5, 19))
    ]

    # Generate all permutations of input_ranges to test if result is order invariant
    permutations = list(itertools.permutations(input_ranges))
    
    for perm in permutations:
        islands = compute_islands(list(perm))
        assert len(islands) == len(expected_islands)
        assert islands == expected_islands
    
test_no_input_ranges()
test_single_input_range()
test_overlapping_input_ranges()
test_middle_spanning_island_item_input_ranges()
test_last_range_contained_within_island()
test_last_range_extends_island()
test_permutation_invariance()