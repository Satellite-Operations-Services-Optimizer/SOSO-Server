from sqlalchemy.sql import ClauseElement
from sqlalchemy.sql.expression import func

def min_max_norm_column(self, column: ClauseElement, partition_by: list[ClauseElement] = None) -> ClauseElement:
    partition_by = partition_by or []
    return (column - func.min(column).over(partition_by=partition_by)) / (func.max(column).over(partition_by=partition_by) - func.min(column).over(partition_by=partition_by))