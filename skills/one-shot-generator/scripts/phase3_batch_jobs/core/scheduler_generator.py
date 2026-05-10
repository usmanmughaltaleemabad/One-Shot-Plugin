"""
Scheduler Generator - Scheduled job generation

Generates:
- Cron jobs
- Periodic tasks
- One-time scheduled jobs
- Job scheduling logic
"""

from typing import Dict, Any


class SchedulerGenerator:
    """Generate job scheduling code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_celery_beat_schedule(self) -> str:
        """Generate Celery Beat schedule"""
        return """
from celery.schedules import crontab
from celery_app import app

# Configure periodic tasks
app.conf.beat_schedule = {
    'process-data-hourly': {
        'task': 'tasks.process_data',
        'schedule': crontab(minute=0),  # Run every hour
        'args': (),
        'kwargs': {},
    },
    'cleanup-old-jobs-daily': {
        'task': 'tasks.cleanup_old_jobs',
        'schedule': crontab(hour=2, minute=0),  # Run at 2 AM daily
        'args': (),
        'kwargs': {},
    },
    'generate-reports-weekly': {
        'task': 'tasks.generate_reports',
        'schedule': crontab(day_of_week=0, hour=0, minute=0),  # Run every Monday at midnight
        'args': (),
        'kwargs': {},
    },
}

# Schedule a one-time job
def schedule_once(task_name, countdown=60):
    from celery_app import app
    task = app.send_task(task_name, countdown=countdown)
    return task.id

# Reschedule a task
def reschedule_task(task_id, countdown=60):
    from celery.result import AsyncResult
    result = AsyncResult(task_id)
    # Celery doesn't have built-in reschedule, need to revoke and resend
    result.revoke(terminate=True)
    # Re-send task
    pass
"""

    def generate_rq_schedule(self) -> str:
        """Generate RQ schedule"""
        return """
from rq_scheduler import Scheduler
from redis import Redis
from jobs import process_data, cleanup_old_jobs

redis_conn = Redis()
scheduler = Scheduler(connection=redis_conn)

# Schedule periodic jobs
scheduler.schedule(
    scheduled_time=datetime.utcnow(),
    func=process_data,
    interval=3600,  # Run every hour
    repeat=-1  # Repeat indefinitely
)

scheduler.schedule(
    scheduled_time=datetime.utcnow() + timedelta(hours=2),
    func=cleanup_old_jobs,
    interval=86400,  # Run daily
    repeat=-1
)

# Schedule one-time job
def schedule_once(func, countdown_seconds=60):
    scheduled_time = datetime.utcnow() + timedelta(seconds=countdown_seconds)
    job = scheduler.schedule(
        scheduled_time=scheduled_time,
        func=func,
    )
    return job.id
"""

    def generate_bull_schedule(self) -> str:
        """Generate Bull queue schedule"""
        return """
import Queue from 'bull';
import cron from 'cron';
import Redis from 'ioredis';

const redis = new Redis();
const jobQueue = new Queue('job-queue', { redis });

// Setup repeating jobs
jobQueue.add(
    { task: 'process-data' },
    {
        repeat: {
            cron: '0 * * * *', // Every hour
        },
    }
);

jobQueue.add(
    { task: 'cleanup-old-jobs' },
    {
        repeat: {
            cron: '0 2 * * *', // Every day at 2 AM
        },
    }
);

// Schedule one-time job
export async function scheduleOnce(jobData, delayMs = 60000) {
    const job = await jobQueue.add(jobData, {
        delay: delayMs,
    });
    return job.id;
}

// Cancel scheduled job
export async function cancelScheduledJob(jobId) {
    const job = await jobQueue.getJob(jobId);
    if (job) {
        await job.remove();
        return true;
    }
    return false;
}
"""


def generate_scheduler(framework: str, language: str) -> Dict[str, str]:
    """
    Generate scheduler code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = SchedulerGenerator(framework, language)
    output = {}

    if language == "python":
        output["scheduler.py"] = generator.generate_celery_beat_schedule()
        output["scheduler_rq.py"] = generator.generate_rq_schedule()
    elif language == "javascript":
        output["scheduler.js"] = generator.generate_bull_schedule()

    return output
