CRONJOBS = [
    ('*/5 * * * *', 'crm.cron.log_crm_heartbeat', 'django_crontab'),
    ('0 */12 * * *', 'crm.cron.update_low_stock'),
]
#----------------

INSTALLED_APPS += [
    'django_celery_beat',
]

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'generate-crm-report': {
        'task': 'crm.tasks.generate_crm_report',
        'schedule': crontab(day_of_week='mon', hour=6, minute=0),
    },
}
