from sqlalchemy.sql import ClauseElement, Window
from sqlalchemy.sql.expression import func

def min_max_norm_column(self, column: ClauseElement, partition_by: list[ClauseElement] = None) -> ClauseElement:
    window = Window() if partition_by is None else Window().partition_by(*partition_by)
    return (column - func.min(column).over(window)) / (func.max(column).over(window) - func.min(column).over(window))
