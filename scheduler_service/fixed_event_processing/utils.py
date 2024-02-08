from typing import List, Optional, Any
from datetime import datetime
from sqlalchemy import Column, func, union, insert
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
    overlapping_processing_blocks = session.query(processing_block_table).filter(
        processing_block_table.time_range.op('&&')(func.tstzrange(start_time, end_time, '[]'))
    ).subquery()


    prev_block_time_range = func.lag(
        overlapping_processing_blocks.c.time_range
    ).over(partition_by=partition_keys, order_by=overlapping_processing_blocks.c.time_range)
    current_block_time_range = overlapping_processing_blocks.c.time_range

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

