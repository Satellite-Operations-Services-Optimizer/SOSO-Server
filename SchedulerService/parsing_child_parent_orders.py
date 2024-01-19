import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.sql import ImageOrder, ScheduleRequest

# Initialize your session
session = Session()

# Parse the image order
def parse_order(order_json):
    order = json.loads(order_json)
    recurrence = order.get('Recurrence', {})
    revisit = recurrence.get('Revisit', 'False') == 'True'
    number_of_revisits = int(recurrence.get('NumberOfRevisits', 0))
    revisit_frequency = int(recurrence.get('RevisitFrequency', 0))
    revisit_frequency_units = recurrence.get('RevisitFrequencyUnits', 'Days')

    # Convert times to datetime objects
    image_start_time = datetime.strptime(order['ImageStartTime'], '%Y-%m-%dT%H:%M:%S')
    image_end_time = datetime.strptime(order['ImageEndTime'], '%Y-%m-%dT%H:%M:%S')
    delivery_time = datetime.strptime(order['DeliveryTime'], '%Y-%m-%dT%H:%M:%S')

    # Calculate duration
    duration = image_end_time - image_start_time

    # Determine revisit frequency in the correct units
    if revisit_frequency_units == 'Days':
        revisit_frequency = timedelta(days=revisit_frequency)
    elif revisit_frequency_units == 'Hours':
        revisit_frequency = timedelta(hours=revisit_frequency)
    elif revisit_frequency_units == 'Weeks':
        revisit_frequency = timedelta(weeks=revisit_frequency)

    # Create the parent order
    parent_order = ImageOrder(
        start_time=image_start_time,
        end_time=image_end_time,
        duration=duration,
        delivery_deadline=delivery_time,
        number_of_revisits=number_of_revisits if revisit else 1,
        revisit_frequency=revisit_frequency,
        priority=order['Priority']
    )

    session.add(parent_order)
    session.commit()

    # Create child orders if necessary
    if revisit:
        for i in range(number_of_revisits):
            # Calculate the new times
            new_start_time = image_start_time + (i+1) * revisit_frequency
            new_end_time = image_end_time + (i+1) * revisit_frequency
            new_delivery_time = delivery_time + (i+1) * revisit_frequency

            child_order = ScheduleRequest(
                schedule_id=parent_order.id,
                window_start=new_start_time,
                window_end=new_end_time,
                duration=duration,
                delivery_deadline=new_delivery_time
            )

            session.add(child_order)

        session.commit()

# Iterate over all the orders in the task_order table
for parent_order in session.query(ImageOrder).all():
    # If the order has revisits, create child orders
    if parent_order.number_of_revisits > 1:
        for i in range(1, parent_order.number_of_revisits):

            # Create a child order
            child_order = ScheduleRequest(
                order_id = parent_order.id,
                window_start = parent_order.start_time,
                window_end = parent_order.end_time,
                duration = parent_order.duration,
                delivery_deadline = parent_order.delivery_time
            )

            # Calculate the new times
            parent_order.start_time = parent_order.start_time + i * parent_order.revisit_frequency
            parent_order.end_time = parent_order.end_time + i * parent_order.revisit_frequency
            parent_order.delivery_time = parent_order.delivery_deadline + i * parent_order.revisit_frequency

            # Add the child order to the session
            session.add(child_order)

        # Commit the session
        session.commit()

# Close the session
session.close()
