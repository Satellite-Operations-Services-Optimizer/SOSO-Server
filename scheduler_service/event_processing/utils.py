from typing import List, Optional, Any, Union, Callable, Type
from datetime import datetime
from sqlalchemy import Column, func, union, insert, and_, not_, select, column, case, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import Alias
import time

from app_config import get_db_session
from ..schedulers.utils import query_gaps

def retrieve_and_lock_unprocessed_blocks_for_processing(
        start_time: datetime,
        end_time: datetime,
        processing_block_table: Any, # orm-mapped table class
        partition_column_names: List[str],
        valid_partition_values_subquery
):
    """
    Retrieves unprocessed blocks from the database if they exist, and creates them if they don't
    WARNING: This function locks some rows in the database and doesn't release the lock until the transaction is committed. Make sure to commit to the database soon after calling this function to release lock.
    """

    if partition_column_names and type(partition_column_names[0]) != str:
        partition_column_names = [col.name for col in partition_column_names]
    partition_columns = [column(col_name) for col_name in partition_column_names]

    session = get_db_session()
    processing_gaps_query = query_gaps(
        source_subquery=session.query(processing_block_table).subquery(),
        range_column=column('time_range'),
        start_time=start_time,
        end_time=end_time,
        partition_columns=partition_columns
    )

    # Define the subquery that selects rows from processing_block_table that match the partition_columns
    processing_block_subquery = session.query(processing_block_table).filter(
        and_(*(valid_partition_values_subquery.c[column_name] == processing_block_table.__table__.c[column_name] for column_name in partition_column_names))
    ).exists()

    # Define the query that selects rows from valid_partition_values_subquery where there's no match in processing_block_table
    missing_partitions = select(
        *partition_columns,
        func.tstzrange(start_time, end_time).label('time_range')
    ).select_from(valid_partition_values_subquery).where(
        not_(processing_block_subquery)
    )

    blocks_to_process = union(processing_gaps_query, missing_partitions)


    # There is an exclusive constraint to prevent overlapping time range for same partition.
    # If two processes query
    columns_to_insert = partition_column_names + ['time_range']
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