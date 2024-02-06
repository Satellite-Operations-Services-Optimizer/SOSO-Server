from app_config.database.mapping import ImageOrder, ObservationOpportunity, ProcessedObservationPeriods
from app_config import get_db_session

def populate_observation_opportunities():
    session = get_db_session()
    image_orders = session.query(ImageOrder).filter(
        ImageOrder.observation_opportunities_processed==False
    ).order_by(ImageOrder.start_time).all()