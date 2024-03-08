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
        filters,
        valid_partition_values_subquery
):
    """
    Retrieves unprocessed blocks from the database if they exist, and creates them if they don't
    WARNING: This function locks some rows in the database and doesn't release the lock until the transaction is committed. Make sure to commit to the database soon after calling this function to release lock.
    """
    session = get_db_session()

    if partition_column_names and type(partition_column_names[0]) != str:
        partition_column_names = [col.name for col in partition_column_names]
    partition_columns = [column(col_name) for col_name in partition_column_names]

    processing_blocks = session.query(processing_block_table)
    if len(filters)>0:
        processing_blocks.filter(*filters)
    processing_blocks = processing_blocks.subquery()

    query_blocks_to_process = query_gaps(
        source_subquery=processing_blocks,
        range_column=column('time_range'),
        start_time=start_time,
        end_time=end_time,
        partition_columns=partition_columns,
        valid_partition_values_subquery=valid_partition_values_subquery
    )

    # There is an exclusive constraint to prevent overlapping time range for same partition.
    # If two processes query
    columns_to_insert = partition_column_names + ['time_range']
    while True:
        try:
            insert_stmt = insert(processing_block_table).from_select(columns_to_insert, query_blocks_to_process)
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
    query_blocks_to_process = session.query(processing_block_table).filter(
        processing_block_table.time_range.op('&&')(func.tstzrange(start_time, end_time)),
        processing_block_table.status == 'processing'
    ).with_for_update().all()
    return query_blocks_to_process