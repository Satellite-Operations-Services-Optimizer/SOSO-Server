from apscheduler.schedulers.background import BackgroundScheduler
from scheduler_service.fixed_event_processing.contact_events import ensure_contact_events_populated
from scheduler_service.fixed_event_processing.eclipse_events import ensure_eclipse_events_populated

scheduler = BackgroundScheduler()

scheduler.add_job(ensure_eclipse_events_populated(), 'interval', hours=1)

scheduler.add_job(ensure_contact_events_populated(), 'interval', hours=1)