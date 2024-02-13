from typing import List, Optional, Any
from datetime import datetime
from sqlalchemy import Column, func, union, insert, or_, and_, not_, over, select, text
from sqlalchemy.exc import IntegrityError
import time

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

    partition_columns_text = [text(col.name) for col in partition_columns]
    # Define the query that selects rows from valid_partition_values_subquery where there's no match in processing_block_table
    missing_partitions = select(
        *partition_columns_text,
        func.tstzrange(start_time, end_time).label('time_range')
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
            time.sleep(0.1)


    # query all processing blocks whose state are 'processing' and whose time range overlaps with the given time range
    blocks_to_process = session.query(processing_block_table).filter(
        processing_block_table.time_range.op('&&')(func.tstzrange(start_time, end_time)),
        processing_block_table.status == 'processing'
    ).with_for_update().all()
    return blocks_to_process

def query_processing_gaps(start_time: datetime, end_time: Optional[datetime], processing_block_table, partition_columns: List[Column]):
    if start_time >= end_time:
        return []
    

    session = get_db_session()
    partition_column_names = [col.name for col in partition_columns]

    # We want to get the gaps between the processingcolumns of a given partition, not between all processing blocks
    # partition_window = over(
    #     order_by=processing_block_table.time_range,
    #     partition_by=partition_columns
    # )

    main_time_range = func.tstzrange(start_time, end_time)
    table_partition_columns = [processing_block_table.__table__.c[column_name] for column_name in partition_column_names]
    processing_blocks = session.query(
        *table_partition_columns,
        processing_block_table.time_range,
        func.lag(processing_block_table.time_range).over(
            partition_by=partition_column_names,
            order_by=processing_block_table.time_range
        ).label('prev_time_range')
    ).subquery()


    # Get the gap between the current block and previous block (bounded by the start_time and end_time)
    # Produces zero-width time ranges if there exists no gap between the current block and the previous block within start_time and end_time
    prev_block_end = func.coalesce(func.upper(processing_blocks.c.prev_time_range), start_time)
    curr_block_start = func.lower(processing_blocks.c.time_range)
    preceding_gap_time_range = func.tstzrange(
        func.least(func.greatest(prev_block_end, start_time), end_time),
        func.greatest(func.least(curr_block_start, end_time), start_time)
    ).label('time_range')

    subquery_partition_columns = [processing_blocks.c[column_name] for column_name in partition_column_names]
    gaps_query_main = session.query(
        *subquery_partition_columns,
        preceding_gap_time_range.label('time_range')
    ).filter(
        preceding_gap_time_range.op('&&')(main_time_range),
        func.lower(text('time_range')) < func.upper(text('time_range')) # TODO: maybe not needed. guaranteed by the above logic I believe
    )

    # We did not consider the gaps that come after the last processing block.
    # Let us include all those 'trailing' gaps
    last_processing_block_end = func.max(func.upper(processing_blocks.c.time_range)) # make sure to group by partition columns
    trailing_gap_time_range = func.tstzrange(
        func.least(func.greatest(last_processing_block_end, start_time), end_time),
        end_time
    ).label('time_range')
    trailing_gaps_query = session.query(
        *subquery_partition_columns,
        trailing_gap_time_range.label('time_range')
    ).filter(
        func.lower(text('time_range')) < func.upper(text('time_range'))
    ).group_by(*subquery_partition_columns)


    unfiltered_processing_gaps = union(gaps_query_main, trailing_gaps_query).subquery()
    # Some zero-width time ranges might have been created, so we need to filter them out
    processing_gaps_query = session.query(unfiltered_processing_gaps).filter(
        ~func.isempty(unfiltered_processing_gaps.c.time_range)
    )
    return processing_gaps_query