from .database import Base

_db_table_class_names = []
def assign_database_table_classes():
    """
    Create classes corresponding to the tables in the database (but in camel case. e.g. table_name -> TableName)
    """
    global _db_table_class_names

    # delete currently exported
    for assigned_class_name in _db_table_class_names:
        del globals()[assigned_class_name]
    _db_table_class_names = []

    for table in Base.classes:
        assigned_class_name = snake_to_camel_case(table.__name__)
        globals()[assigned_class_name] = table
        _db_table_class_names.append(assigned_class_name)

def snake_to_camel_case(input_string):
    words = input_string.split('_')  # Assuming input_string is snake_case
    return ''.join([word.capitalize() for word in words[:]])

assign_database_table_classes()
