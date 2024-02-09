from typing import List, Optional, Any
from datetime import datetime
from sqlalchemy import Column, func, union, insert, or_, and_
from sqlalchemy.exc import IntegrityError

from app_config.database.mapping import ImageOrder, ObservationOpportunity, ProcessedObservationBatch
from app_config import get_db_session
from utils import query_processing_gaps

def retrieve_and_lock_unprocessed_blocks_for_processing(
        start_time: datetime,
        end_time: datetime,
        processing_block_table: Any, # orm-mapped table class
        partition_columns: List[Column]
):
    """
    WARNING: This function locks some rows in the database and doesn't release the lock until the transaction is committed.
    It retrieves unprocessed blocks from the database if they exist, and creates them if they don't
    """

    session = get_db_session()
    gaps_query = query_processing_gaps(
        start_time,
        end_time,
        processing_block_table,
        *partition_columns
    )

    missing_partitions = 

    # There is an exclusive constraint to prevent overlapping time range for same partition.
    # If two processes query
    while True:
        try:
            insert(processing_block_table).from_select(gaps_query)
            session.commit()
            break
        except IntegrityError:
            # If multiple processes are trying to populate the same time range,
            # there might come a case where a process has already populated a 
            # gap (or partially populated a gap) that we are trying to populate.
            # In such a case, it is unfortunately impossible to partially rollback only
            # the rows that violate. we have to rollback everything and retry the whole thing.
            session.rollback()


    # query all processing blocks whose state are 'processing' and whose time range overlaps with the given time range
    blocks_to_process = session.query(processing_block_table).filter(
        processing_block_table.time_range.op('&&')(func.tstzrange(start_time, end_time, '[]')),
        processing_block_table.state == 'processing'
    ).with_for_update().all()
    return blocks_to_process

def query_processing_gaps(start_time: datetime, end_time: Optional[datetime], processing_block_table, partition_keys: List[Column]):
    if start_time >= end_time:
        return []

    session = get_db_session()

    # We want to get the gaps between the processing blocks of a given partition, not between all processing blocks
    partition_window = func.partition_by(*partition_keys).order_by(processing_block_table.time_range)

    overlapping_condition = processing_block_table.time_range.op('&&')(func.tstzrange(start_time, end_time, '[]'))
    overlapping_processing_blocks = session.query(
        *partition_keys,
        processing_block_table.time_range,
        func.lag(processing_block_table.time_range).over(partition_window).label('prev_time_range'),
        func.lead(processing_block_table.time_range).over(partition_window).label('next_time_range')
    ).filter(overlapping_condition).subquery()

    # Get the gaps between processed batches, bounded by the start and end time (including edge case where there's a gap between the start time and the first batch)
    gap_time_range = func.tstzrange(
        func.greatest(func.coalesce(overlapping_processing_blocks.prev_time_range.upper, start_time), start_time),
        func.greatest(current_block_time_range.lower, start_time) # when there's no batch within start_time and end_time, it gives the range (start_time, start_time), which will be filtered out
    ).subquery()
        
    gaps_query_main = session.query(
        *partition_keys,
        gap_time_range.label('time_range')
    ).filter(gap_time_range.lower < gap_time_range.upper).subquery()

    # Handle the case where there's a gap between the last processing bacth and the end time,
    # as well as when there's no processing batches at all between the start and end time
    gaps_query_end_edge_case = session.query(
        *partition_keys,
        func.tstzrange(func.greatest(func.max(current_block_time_range.upper), start_time), end_time)
    ).group_by(*partition_keys).subquery()

    processing_gaps = union(gaps_query_main, gaps_query_end_edge_case).order_by('time_range')

    gaps = session.query(
        *partition_keys,
        func.coalesce(overpalling_processing_blocks.prev)
    )

    prev_and_next_block_time_range = session.query(
        processing_block_table
    )


    time_range_query = func.tstzrange(start_time, end_time, '[]')

    # To get all gaps, we need to get all processing blocks that overlap with the given time, as well as the blocks that come right before and after the given time range
    # so that we can get the gaps in between them (bounded by the start_time and end_time of course)

    # Define the conditions for the overlapping, before and after rows
    overlapping_condition = processing_block_table.time_range.op('&&')(time_range_query)
    before_condition = processing_block_table.time_range.op('&<')(time_range_query)
    after_condition = processing_block_table.time_range.op('&>')(time_range_query)

    # Get the row that comes right before the first overlapping row, partitioned by the partition keys
    before_row_subquery = session.query(*partition_keys, func.max(processing_block_table.time_range).label('time_range')).filter(before_condition).group_by(*partition_keys).subquery()
    # Get the row that comes right after the last overlapping row, partitioned by the partition keys
    after_row_subquery = session.query(*partition_keys, func.min(processing_block_table.time_range).label('time_range')).filter(after_condition).group_by(*partition_keys).subquery()
    # Define the subquery that selects all rows that overlap with the given time range
    overlapping_processing_blocks = session.query(processing_block_table).filter(overlapping_condition).subquery()

    # Combine the overlapping, before, and after rows into one subquery
    overlapping_and_adjacent_processing_blocks = session.query(processing_block_table).filter(
        or_(
            overlapping_condition,
            and_
        )
    )



    # define the subquery that selects all rows that overlap with the given time range
    overlapping_processing_blocks = session.query(processing_block_table).filter(
        processing_block_table.time_range.op('&&')(func.tstzrange(start_time, end_time, '[]'))
    ).subquery()

    # define the query that selects the row with the maximum end time that is less than or equal to the start time
    before_row = session.query(processing_block_table).filter(
        processing_block_table.time_range.op('&<')(func.tstzrange(start_time, end_time, '[]'))
    ).order_by(processing_block_table.time_range.desc()).limit(1).subquery()

    # define the query that selects the row with the minimum start time that is greater than or equal to the end time
    after_row = session.query(processing_block_table).filter(
        processing_block_table.time_range.op('&>')(func.tstzrange(start_time, end_time, '[]'))
    ).order_by(processing_block_table.time_range).limit(1).subquery()

    # define the final query for both overlapping and adjacent blocks.
    # This is required so that we can grab the whole time range (start_time and end_time) even if we have no
    # processing blocks that overlap the time range.
    overlapping_and_adjacent_processing_blocks = session.query(overlapping_processing_blocks).union_all(
        session.query(before_row)
    ).union_all(session.query(after_row))

    prev_block_time_range = func.lag(
        overlapping_and_adjacent_processing_blocks.c.time_range
    ).over(partition_by=partition_keys, order_by=overlapping_and_adjacent_processing_blocks.c.time_range)
    current_block_time_range = overlapping_and_adjacent_processing_blocks.c.time_range

    # Get the gaps between processed batches, bounded by the start and end time (including edge case where there's a gap between the start time and the first batch)
    gap_time_range = func.tstzrange(
        func.greatest(func.coalesce(prev_block_time_range.upper, start_time), start_time),
        func.greatest(current_block_time_range.lower, start_time) # when there's no batch within start_time and end_time, it gives the range (start_time, start_time), which will be filtered out
    )

    gaps_query_main = session.query(
        *partition_keys,
        gap_time_range.label('time_range')
    ).filter(gap_time_range.lower < gap_time_range.upper)

    # Handle the case where there's a gap between the last bacth and the end time, as well as when there's no batches at all between the start and end time
    gaps_query_end_edge_case = session.query(
        *partition_keys,
        func.tstzrange(func.greatest(func.max(current_block_time_range.upper), start_time), end_time)
    ).filter(
        func.max(current_block_time_range.upper) < end_time # so we don't get zero-width ranges, or ranges where the start time is greater than the end time
    )

    processing_gaps = union(gaps_query_main, gaps_query_end_edge_case).order_by('time_range')
    return processing_gaps

