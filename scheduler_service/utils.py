from datetime import datetime
from typing import Optional
from sqlalchemy import Column, column, func, case, or_, union, text, not_
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

def copy_schedule(self, schedule: Schedule, time_range: TimeHorizon = TimeHorizon(None, None),  **options: Optional[dict]):
    """

    """
    session = get_db_session()
    new_schedule = Schedule(name=f"{schedule.name} - Copy_{datetime.now()}")
    session.add(new_schedule)

    copy_options = {
        'copied_schedule_request_types': ['received'],
        'context_duration': None,
        'context_event_types': ['outage', 'contact', 'eclipse'],
        'backpopulate_contact_events': True
    }
    copy_options.update(options)
    if time_range.start is None:
        copy_options['lookback_duration'] = None
    
    if copy_options['lookback_duration'] is not None:
        fixed_event_lookback_time_range = TimeHorizon(time_range.start - copy_options['lookback_duration'])
        fixed_event_lookback_constraint = (ScheduledEvent.event_type=='fixed')



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
        start_time: datetime,
        end_time: Optional[datetime],
        source_subquery,
        range_column: column,
        partition_columns: List[str],
        range_constructor: Callable = func.tstzrange
    ):
    if start_time >= end_time:
        return []

    session = get_db_session()

    if start_time is None:
        start_time = datetime.min
    if end_time is None:
        end_time = datetime.max

    main_time_range = range_constructor(start_time, end_time, '[]')
    table_partition_columns = [source_subquery.c[column.name] for column in partition_columns]
    processing_blocks = session.query(
        *table_partition_columns,
        range_column.label('time_range'),
        func.lag(range_column).over(
            partition_by=partition_columns,
            order_by=range_column
        ).label('prev_time_range')
    ).subquery()


    # Get the gap between the current block and previous block (bounded by the start_time and end_time)
    # Produces zero-width time ranges if there exists no gap between the current block and the previous block within start_time and end_time
    prev_block_end = func.coalesce(func.upper(processing_blocks.c.prev_time_range), start_time)
    curr_block_start = func.lower(processing_blocks.c.time_range)
    preceding_gap_time_range = range_constructor(
        func.least(func.greatest(prev_block_end, start_time), end_time),
        func.greatest(func.least(curr_block_start, end_time), start_time)
    ).label('time_range')

    subquery_partition_columns = [processing_blocks.c[column.name] for column in partition_columns]
    gaps_query_main = session.query(
        *subquery_partition_columns,
        preceding_gap_time_range.label('time_range')
    ).filter(
        preceding_gap_time_range.op('&&')(main_time_range),
        func.lower(column('time_range')) < func.upper(column('time_range')) # TODO: maybe not needed. guaranteed by the above logic I believe
    )

    # We did not consider the gaps that come after the last processing block.
    # Let us include all those 'trailing' gaps
    last_processing_block_end = func.max(func.upper(processing_blocks.c.time_range)) # make sure to group by partition columns
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


    unfiltered_processing_gaps = union(gaps_query_main, trailing_gaps_query).subquery()
    # Some zero-width time ranges might have been created, so we need to filter them out
    processing_gaps_query = session.query(unfiltered_processing_gaps).filter(
        ~func.isempty(unfiltered_processing_gaps.c.time_range)
    )
    return processing_gaps_query

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

    main_time_range = range_constructor(start_time, end_time)
    table_range_column = source_subquery.c[range_column.name]
    table_partition_columns = [source_subquery.c[column.name] for column in partition_columns]

    prev_island_end_time = func.max(func.upper(table_range_column)).over(
        order_by=table_range_column, partition_by=table_partition_columns, rows=(None, -1)
    ).label('prev_island_end_time')
    next_time_range = func.lead(range_column).over(order_by=table_range_column, partition_by=partition_columns)

    island_markers_subquery = session.query(
        *table_partition_columns,
        prev_island_end_time,
        table_range_column,
        case(
            (prev_island_end_time==None, True),
            (prev_island_end_time<func.lower(table_range_column), True),
            else_=False
        ).label('is_new_island_start'),
        case((next_time_range==None, True), else_=False).label('is_last_row')
    ).filter(
        range_column.op('&&')(main_time_range)
    ).subquery()

    # This optimization is using the assumption that with assumption that the "LEAD" clause (func.lead) is computed before the filter "WHERE" clause in postgresql
    # we need to get the end of the current island by looking at the *next* island, not the next row.
    # that's why we order by is_new_island_start, because we want lead over the rows where is_new_island_start is true (let's call those rows the island_start_markers).
    # The last rows within a partition can be the end of an island without being the start of a new island.
    # So we want to put them right after all the island_start_marker rows.
    # We only care about island_start_marker rows, and the last rows of the partitions because they are the ones where we
    # get our island's range from since they have the most up-to-date island end time (that is why we order by them, so they come frist in our result set, saving computation).
    # The other rows will be filtered out in our query.
    ending_island_end_time = case(
        (island_markers_subquery.c.is_new_island_start==True, island_markers_subquery.c.prev_island_end_time),
        else_=func.greatest(func.upper(range_column), island_markers_subquery.c.prev_island_end_time)
    )
    current_island_end_time = func.lead(ending_island_end_time).over(
        order_by=[
            island_markers_subquery.c.is_new_island_start.desc(),  # perform the lead over the rows where is_new_island_start is true in descending order
            island_markers_subquery.c.is_last_row.desc(), # we want the ending rows to come right after the island start markers.
            island_markers_subquery.c[range_column.name]
        ],
        partition_by=partition_columns
    )

    # In the query below, the expression `func.greatest(current_island_end_time, func.upper(range_column))`
    # handles two edge cases: 
    #   1. case when nothing comes after this row (and thus current_island_end_time is null) and
    #   2. case when markers that are not island start markers, and are also not last rows,
    #      start to show up in the order. (we don't want to consider these rows, because 
    #      they give us incorrect data)
    # in both cases, we set the end time to upper(range_column)
    island_partitions = [island_markers_subquery.c[column.name] for column in partition_columns]
    islands_query = session.query(
        *island_partitions,
        range_constructor(
            func.lower(range_column),
            func.greatest(current_island_end_time, func.upper(range_column))
        ).label(range_column.name)
    ).filter(island_markers_subquery.c.is_new_island_start==True)
    return islands_query