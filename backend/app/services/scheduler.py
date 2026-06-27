"""APScheduler configuration for background agents."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.agents.silence_detection import run_silence_detection
from app.agents.pattern_agent import run_pattern_agent

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
    
    # Pattern Intelligence: weekly on Sunday at 3:00 AM
    scheduler.add_job(
        run_pattern_agent,
        trigger=CronTrigger(day_of_week="sun", hour=3, minute=0),
        id="pattern_agent_weekly",
        name="Pattern Intelligence Agent - Weekly Analysis",
        replace_existing=True,
    )
    
    scheduler.start()


def shutdown_scheduler():
    """Shutdown scheduler on app exit."""
    scheduler.shutdown()
