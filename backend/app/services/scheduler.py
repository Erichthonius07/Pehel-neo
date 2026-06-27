"""APScheduler configuration for background agents."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.agents.silence_detection import run_silence_detection

scheduler = BackgroundScheduler()


def init_scheduler():
    """Start scheduler and register cron jobs."""
    # Silence Detection: daily at 9 AM
    scheduler.add_job(
        run_silence_detection,
        trigger=CronTrigger(hour=9, minute=0),
        id="silence_detection_daily",
        name="Silence Detection Agent - Daily Sweep",
        replace_existing=True,
    )
    scheduler.start()


def shutdown_scheduler():
    """Shutdown scheduler on app exit."""
    scheduler.shutdown()