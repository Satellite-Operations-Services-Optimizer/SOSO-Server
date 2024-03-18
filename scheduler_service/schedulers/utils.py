from datetime import datetime
from typing import Optional
from sqlalchemy import Column, column, func, case, or_, union, text, not_, select, and_, or_, null
from sqlalchemy.sql.expression import BinaryExpression
from dataclasses import dataclass
from app_config.database.mapping import Schedule
from typing import Optional, TypedDict, List, Callable
from datetime import timedelta
from app_config.database.mapping import ScheduledEvent
from app_config import get_db_session

@dataclass
class TimeHorizon:
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    include_overlap: bool = False

    def apply_filters(self, start_time_column: Column, end_time_column: Optional[Column] = None) -> list[BinaryExpression]:
        filters = []

        if self.start is not None:
            start_filter = (start_time_column >= self.start)
            if end_time_column and self.include_overlap:
                start_filter |= (end_time_column >= self.start)
            filters.append(start_filter)
        
        if self.end is not None:
            end_column = end_time_column if end_time_column else start_time_column
            end_filter = (end_column <= self.end)
            if start_time_column and self.include_overlap:
                end_filter |= (start_time_column <= self.end)
            filters.append(end_filter)

        return filters

class CopyOptions(TypedDict, total=False):
    copied_schedule_request_types: List[str]
    lookback_duration: Optional[timedelta]

def copy_requests_into_schedule(schedule_id: int, requests_subquery):
    new_to_old_request_ids = {}
    session = get_db_session()

    session.query(requests_subquery)
    return new_to_old_request_ids

def copy_schedule(schedule_id: int, start_time: datetime, end_time: datetime, time_range: TimeHorizon = TimeHorizon(None, None),  **options: Optional[dict]):
    """
    Copies the events of the provided schedule_id, within the specified time bounds, into a new schedule
    """
    session = get_db_session()
    old_schedule = session.query(Schedule).filter_by(id=schedule_id).one()
    new_schedule = Schedule(name=f"{old_schedule.name} - Copy_{datetime.now()}")
    session.add(new_schedule)
    session.flush()

    # Copy the events of `schedule_id` into a new schedule

    # Copy ScheduleRequest instances that overlap with our span
    schedule_requests_in_span = session.query()


def get_image_dimensions(image_type: str):
    image_type = image_type.lower()
    if image_type == "spotlight":
        return 10, 10
    elif image_type == "medium":
        return 40, 20
    elif image_type == "low":
        return 40, 20

def query_gaps(
        source_subquery,
        range_column: column,
        partition_columns: List[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        range_constructor: Callable = func.tstzrange,
        valid_partition_values_subquery = None
    ):
    session = get_db_session()
    range_column = column(range_column.name)
    partition_columns = [
        column(partition_column) if type(partition_column)==str else column(partition_column.name)
        for partition_column in partition_columns
    ]

    if start_time >= end_time: # return empty result set that still has the correct columns
        return session.query(
            *[null().label(partition_column.name) for partition_column in partition_columns],
            null().label('time_range')
        ).filter(False)

    if start_time is None:
        start_time = datetime.min
    if end_time is None:
        end_time = datetime.max

    window_time_range = range_constructor(start_time, end_time)
    table_partition_columns = [source_subquery.c[column.name] for column in partition_columns]
    blocks = session.query(
        *table_partition_columns,
        range_column.label('time_range'),
        func.lag(range_column).over(
            partition_by=partition_columns,
            order_by=range_column
        ).label('prev_time_range')
    ).subquery()


    # Get the gap between the current block and previous block (bounded by the start_time and end_time)
    # Produces zero-width time ranges if there exists no gap between the current block and the previous block within start_time and end_time
    prev_block_end = func.coalesce(func.upper(blocks.c.prev_time_range), start_time)
    curr_block_start = func.lower(blocks.c.time_range)
    preceding_gap_time_range = range_constructor(
        func.least(func.greatest(prev_block_end, start_time), end_time),
        func.greatest(func.least(curr_block_start, end_time), start_time)
    ).label('time_range')

    subquery_partition_columns = [blocks.c[column.name].label(column.name) for column in partition_columns]
    gaps_query_main = session.query(
        *subquery_partition_columns,
        preceding_gap_time_range.label('time_range')
    ).filter(
        preceding_gap_time_range.op('&&')(window_time_range),
        func.lower(column('time_range')) < func.upper(column('time_range')) # TODO: maybe not needed. guaranteed by the above logic I believe
    )

    # We did not consider the gaps that come after the last processing block.
    # Let us include all those 'trailing' gaps
    last_processing_block_end = func.max(func.upper(blocks.c.time_range)) # make sure to group by partition columns
    trailing_gap_time_range = range_constructor(
        func.least(func.greatest(last_processing_block_end, start_time), end_time),
        end_time
    ).label('time_range')
    trailing_gaps_query = session.query(
        *subquery_partition_columns,
        trailing_gap_time_range.label('time_range')
    ).filter(
        func.lower(column('time_range')) < func.upper(column('time_range'))
    ).group_by(*subquery_partition_columns)


    gaps_query_list = [gaps_query_main, trailing_gaps_query]
    if valid_partition_values_subquery is not None:
        # Handle the case wher there is no anchor block in the partition to compute the gap from
        # (the time range for the partition is empty).
        # In such a case, mark the whole range as a gap

        missing_partitions = session.query(
            *[valid_partition_values_subquery.c[partition_column.name] for partition_column in partition_columns],
            func.tstzrange(start_time, end_time).label('time_range')
        ).outerjoin(
            source_subquery,
            and_(*[source_subquery.c[partition_column.name]==valid_partition_values_subquery.c[partition_column.name] for partition_column in partition_columns])
        ).filter(
            source_subquery.c.time_range == None # remove rows where the partition exists in the source subquery
        )
        gaps_query_list.append(missing_partitions)

    gaps_subquery = union(*gaps_query_list).subquery()

    # Some zero-width time ranges might have been created, so we need to filter them out
    filtered_gaps_query = session.query(
        *[gaps_subquery.c[partition_column.name] for partition_column in partition_columns],
        gaps_subquery.c.time_range
    ).filter(
        ~func.isempty(gaps_subquery.c.time_range)
    )
    return filtered_gaps_query

def query_islands(
        source_subquery,
        range_column: column,
        partition_columns: List[str] = [],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        range_constructor: Callable = func.tstzrange
    ):
    """
    A *hopefully* efficient solution to the gaps and islands problem.
    Creates non-overlapping time ranges (islands) from potentially overlapping time ranges,
    within each partition.
    """

    session = get_db_session()

    if start_time is None:
        start_time = datetime.min
    if end_time is None:
        end_time = datetime.max

    range_column = column(range_column.name)
    partition_columns = [
        column(partition_column) if type(partition_column)==str else column(partition_column.name)
        for partition_column in partition_columns
    ]

    # This value is only valid in rows that are the start of a new island. It is a rolling computation of the previous island's end time, so it will only be accurate once we *just* enter a new island.
    prev_island_end_time = func.max(func.upper(source_subquery.c[range_column.name])).over(
        order_by=range_column, partition_by=partition_columns, rows=(None, -1)
    ).label('prev_island_end_time')
    next_time_range = func.lead(range_column).over(order_by=range_column, partition_by=partition_columns)

    window_time_range = range_constructor(start_time, end_time)
    table_partition_columns = [source_subquery.c[column.name] for column in partition_columns]
    island_markers_subquery = session.query(
        *table_partition_columns,
        prev_island_end_time,
        range_column,
        case(
            (prev_island_end_time==None, True),
            (prev_island_end_time<func.lower(range_column), True),
            else_=False
        ).label('is_new_island_start'),
        case((next_time_range==None, True), else_=False).label('is_last_row')
    ).order_by(range_column).filter(
        range_column.op('&&')(window_time_range)
    ).subquery()

    # This optimization is using the assumption that the "LEAD" clause (func.lead) is computed after the filter "WHERE" clause in postgresql.
    # Check git commit history for the optimization I made for the wrong assumption that "LEAD" clause is computed before the "WHERE" clause, in case it is needed in the future

    # we need to get the end of the current island by looking at the *next* island, not the next row.

    ending_island_end_time = case(
        (island_markers_subquery.c.is_new_island_start==True, island_markers_subquery.c.prev_island_end_time),
        else_=func.greatest(func.upper(range_column), island_markers_subquery.c.prev_island_end_time)
    )

    current_island_end_time = func.lead(ending_island_end_time).over(partition_by=partition_columns, order_by=range_column)
    # This query includes items that are not island start markers, but are last rows. 
    # We need these to get the correct island end times (using the lead function in 
    # variable `current_island_end_time`) but we don't want them in the result set, so we want to filter them from the result set.
    # Since postgresql seems to perform the filter BEFORE the LEAD, that helps us with getting the correct island end time,
    # but that means that we can't directly filter these rows out using the where clause, because it will affect our "LEAD" clause
    # and make it return incorrect data. That is why we have to first subquery, then filter (even though this is not very ideal)
    unfiltered_islands_subquery = select(
        *partition_columns,
        island_markers_subquery.c.is_new_island_start,
        island_markers_subquery.c.time_range.label('original_range'),
        func.lead(island_markers_subquery.c.time_range).over(partition_by=partition_columns).label('next_row_time_range'),
        current_island_end_time.label('curr_island_end'),
        range_constructor(
            func.lower(range_column),
            func.coalesce(current_island_end_time, func.upper(range_column))
        ).label(range_column.name)
    ).where(
        or_(
            island_markers_subquery.c.is_new_island_start==True,
            island_markers_subquery.c.is_last_row==True
        )
    ).subquery()
    islands_query = session.query(
        *partition_columns,
        range_column
    ).filter(unfiltered_islands_subquery.c.is_new_island_start==True)
    return islands_query