from typing import List, Optional, Any
from datetime import datetime
from sqlalchemy import Column, func, union, insert, or_, and_, not_, over, select, text
from sqlalchemy.exc import IntegrityError

from app_config import get_db_session

def retrieve_and_lock_unprocessed_blocks_for_processing(
        start_time: datetime,
        end_time: datetime,
        processing_block_table: Any, # orm-mapped table class
        partition_columns: List[Column],
        valid_partition_values_subquery
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
        partition_columns
    )

    # Define the subquery that selects rows from processing_block_table that match the partition_columns
    processing_block_subquery = session.query(processing_block_table).filter(
        and_(*(valid_partition_values_subquery.c[column.name] == column for column in partition_columns))
    ).exists()

    # Define the query that selects rows from valid_partition_values_subquery where there's no match in processing_block_table
    missing_partitions = select(
        *[text(col.name) for col in partition_columns],
        func.tstzrange(start_time, end_time, '[]').label('time_range')
    ).select_from(valid_partition_values_subquery).where(
        not_(processing_block_subquery)
    )

    blocks_to_process = union(gaps_query, missing_partitions)


    # There is an exclusive constraint to prevent overlapping time range for same partition.
    # If two processes query
    columns_to_insert = [col.name for col in partition_columns] + ['time_range']
    while True:
        try:
            insert_stmt = insert(processing_block_table).from_select(columns_to_insert, blocks_to_process)
            session.execute(insert_stmt)
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
        processing_block_table.status == 'processing'
    ).with_for_update().all()
    return blocks_to_process

def query_processing_gaps(start_time: datetime, end_time: Optional[datetime], processing_block_table, partition_columns: List[Column]):
    if start_time >= end_time:
        return []

    session = get_db_session()

    # We want to get the gaps between the processingcolumns of a given partition, not between all processing blocks
    # partition_window = over(
    #     order_by=processing_block_table.time_range,
    #     partition_by=partition_columns
    # )

    main_time_range = func.tstzrange(start_time, end_time, '[]')
    processing_blocks = session.query(
        *partition_columns,
        processing_block_table.time_range,
        func.lag(processing_block_table.time_range).over(
            partition_by=partition_columns,
            order_by=processing_block_table.time_range
        ).label('prev_time_range'),
        func.lead(processing_block_table.time_range).over(
            partition_by=partition_columns,
            order_by=processing_block_table.time_range
        ).label('next_time_range')
    ).subquery()

    # Get the gaps between processed batches, bounded by the start and end time
    # it gets whole range [start_time, end_time] when the first (or the only) block is after the range
    # it gets the range [start_time, start_time] when the only block is before the range (or when there is no overlapping block, but the first non-overlapping block is before the range)
    # it gets [start_time, block.lower] when the first block is contained in the range (or when first overlapping block is contained in range)
    # it gets  (including edge case where there's a gap between the start time and the first batch)
    gap_time_range = func.tstzrange(
        func.greatest(func.coalesce(func.upper(processing_blocks.c.prev_time_range), start_time), start_time),
        func.greatest(func.least(func.lower(processing_blocks.c.time_range), end_time), start_time) # when there's no batch within start_time and end_time, it gives the range (start_time, start_time), which will be filtered out
    ).label('time_range')
        
    gaps_query_main = session.query(
        *partition_columns,
        gap_time_range.label('time_range')
    ).filter((func.lower(gap_time_range) < func.upper(gap_time_range)) & gap_time_range.op('&&')(main_time_range))

    # gets the last block's upper bound to end_time
    gaps_query_end_edge_case = session.query(
        *partition_columns,
        func.tstzrange(func.greatest(func.max(func.upper(processing_blocks.c.time_range)), start_time), end_time)
    ).filter(func.upper(processing_blocks.c.time_range) > end_time).group_by(*partition_columns)

    unfiltered_processing_gaps = union(gaps_query_main, gaps_query_end_edge_case).subquery()

    # Some zero-width time ranges might have been created, so we need to filter them out
    processing_gaps_query = session.query(unfiltered_processing_gaps).filter(
        ~func.isempty(unfiltered_processing_gaps.c.time_range)
    )
    return processing_gaps_query