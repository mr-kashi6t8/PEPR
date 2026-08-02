from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "pepr_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
)

import json
import os
from celery.schedules import crontab

# Ingestion Scheduler
celery_app.conf.beat_schedule = {}

config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'sources.json')
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config_data = json.load(f)
        for idx, source in enumerate(config_data.get('sources', [])):
            schedule_parts = source.get('schedule', '0 0 * * *').split()
            if len(schedule_parts) == 5:
                celery_app.conf.beat_schedule[f"ingest_{source['id']}"] = {
                    'task': 'app.services.ingestion.tasks.run_ingestion_task',
                    'schedule': crontab(
                        minute=schedule_parts[0],
                        hour=schedule_parts[1],
                        day_of_month=schedule_parts[2],
                        month_of_year=schedule_parts[3],
                        day_of_week=schedule_parts[4]
                    ),
                    'args': (source['id'], source['type'], source['config'])
                }
