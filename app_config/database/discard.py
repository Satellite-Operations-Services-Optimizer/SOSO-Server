from .setup import engine, Base
from ..logs import logging
from dotenv import load_dotenv
import os
from sqlalchemy import Table, Column, Integer

load_dotenv()

logger = logging.getLogger(__name__)

db_classes = []
def automap_database_to_classes():
    """
    Create classes corresponding to the tables in the database (but in camel case. e.g. table_name -> TableName)
    """
    global db_classes

    # delete currently exported classes
    for db_class in db_classes:
        del globals()[db_class.__name__]
    db_classes = []
    
    
    view_names_str = os.getenv('DB_VIEWS_WITH_ID_FIELD', '')
    view_names = [name.strip() for name in view_names_str.split(',') if name.strip()!=""] # remove empty strings
    # view_classes = map_views_with_id(view_names)
    # for view_class in view_classes:
    #     globals()[view_class.__name__] = view_class
    #     db_classes.append(view_class)

    #     logger.info(f"Auto-assigned database view: {view_class.__name__}")
    
    tables = []
    table_names = set([db_class.removeprefix(f"{Base.metadata.schema}.") for db_class in Base.metadata.tables])
    for table_name in table_names:
        tables.append(Table(table_name, Base.metadata, autoload=True, autoload_with=engine))


    # Automap to reflect all tables in database
    Base.prepare(autoload_with=engine, reflect=True)

    # table_names = set([db_class.__name__ for db_class in Base.classes])
    # remaining_names = all_names-table_names 
    for table_class in Base.classes:
        table_class.__name__ = snake_to_camel_case(table_class.__name__)
        globals()[table_class.__name__] = table_class
        db_classes.append(table_class)

        logger.info(f"Auto-assigned database table: {table_class.__name__}")


def map_views_with_id(view_names: list[str]):
    views = []
    for view_name in view_names:
        assigned_class_name = snake_to_camel_case(view_name)
        views.append(type(assigned_class_name, (Base,), {
            '__tablename__': view_name,
            'id': Column(Integer, primary_key=True),
            '__table_args__': {'autoload': True}
        }))
    return views


def snake_to_camel_case(input_string):
    words = input_string.split('_')  # Assuming input_string is snake_case
    return ''.join([word.capitalize() for word in words[:]])

automap_database_to_classes()
