from sqlalchemy.sql import ClauseElement
from sqlalchemy.sql.expression import func
from sqlalchemy import case

def min_max_norm(column: ClauseElement, partition_by: list[ClauseElement] = None) -> ClauseElement:
    """
    Computes the min/max normalized values of the columns using the well-known min/max norm formula:
    (column - min(column)) / (max(column) - min(column))
    """
    partition_by = partition_by or []
    value_range = func.max(column).over(partition_by=partition_by) - func.min(column).over(partition_by=partition_by)

    norm = (column - func.min(column).over(partition_by=partition_by)) / value_range
    norm_safe = case((value_range == 0, 1), else_=norm) # avoid division by zero, also if all values are the same (i.e. value_range = 0), they are all equally satisfactory, so we return 1
    return norm_safe

def normalized_avg(column: ClauseElement, partition_by: list[ClauseElement] = None) -> ClauseElement:
    """
    Computes the min/max normalized average using the below formula:
    (avg(column) - min(column)) / (max(column) - min(column))
    """
    partition_by = partition_by or []
    value_range = func.max(column).over(partition_by=partition_by) - func.min(column).over(partition_by=partition_by)

    norm_avg = (func.avg(column) - func.min(column).over(partition_by=partition_by)) / value_range
    norm_avg_safe = case((value_range == 0, 1), else_=norm_avg) # avoid division by zero, also if all values are the same (i.e. value_range = 0), they are all equally satisfactory, so we return 1
    return norm_avg_safe

def z_score(column: ClauseElement, partition_by: list[ClauseElement] = None) -> ClauseElement:
    """
    Computes the z-score of the given column using the well-known z-score formula:
    (column - avg(column)) / stddev(column)
    """
    partition_by = partition_by or []
    stddev = func.stddev(column).over(partition_by=partition_by)

    z_score = (column - func.avg(column).over(partition_by=partition_by)) / stddev
    z_score_safe = case((stddev == 0, 0), else_=z_score) # avoid division by zero, also, if stddev=0, they are all 0 standard deviations away from the mean, so set to 0
    return z_score_safe

