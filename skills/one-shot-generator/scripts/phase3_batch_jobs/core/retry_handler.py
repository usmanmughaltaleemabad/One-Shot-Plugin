"""
Retry Handler - Job retry strategies and backoff logic

Generates:
- Exponential backoff
- Jitter strategies
- Retry policies
- Max retry handling
"""

from typing import Dict, Any


class RetryHandler:
    """Generate retry handling code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_celery_retry(self) -> str:
        """Generate Celery retry strategies"""
        return """
from celery import Celery, Task
from celery.utils.log import get_task_logger
import random
import logging

logger = get_task_logger(__name__)

class AutoRetryTask(Task):
    '''Task with auto-retry on specific exceptions'''
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True  # Add random jitter to backoff

def calculate_backoff(retry_count, base_delay=2, max_delay=600):
    '''Calculate exponential backoff with jitter'''
    delay = min(base_delay * (2 ** retry_count), max_delay)
    jitter = random.uniform(0, delay * 0.1)  # Add 10% jitter
    return delay + jitter

def should_retry(exception, retry_count, max_retries=3):
    '''Determine if exception should trigger retry'''
    if retry_count >= max_retries:
        return False

    # Don't retry on validation errors
    if isinstance(exception, ValueError):
        return False

    return True

def retry_with_backoff(task_func, *args, max_retries=3, base_delay=2, **kwargs):
    '''Manually retry task with exponential backoff'''
    last_exception = None
    for attempt in range(max_retries):
        try:
            return task_func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = calculate_backoff(attempt, base_delay)
                logger.warning(f'Attempt {attempt + 1} failed, retrying in {delay}s: {e}')
                import time
                time.sleep(delay)
            else:
                logger.error(f'All {max_retries} retry attempts failed')

    raise last_exception

def deadline_retry(task_id, deadline_seconds=3600):
    '''Retry job up until deadline'''
    from celery_app import app
    from datetime import datetime, timedelta

    deadline = datetime.utcnow() + timedelta(seconds=deadline_seconds)
    attempt = 0

    while datetime.utcnow() < deadline:
        try:
            result = app.AsyncResult(task_id)
            if result.state == 'SUCCESS':
                return result.result
            elif result.state == 'FAILURE':
                attempt += 1
                delay = calculate_backoff(attempt)
                logger.info(f'Retrying job {task_id} in {delay}s')
                import time
                time.sleep(delay)
        except Exception as e:
            logger.error(f'Error checking job: {e}')

    raise TimeoutError(f'Job {task_id} exceeded deadline')
"""

    def generate_rq_retry(self) -> str:
        """Generate RQ retry strategies"""
        return """
from rq import Queue
from rq.job import JobStatus
from redis import Redis
import random
import logging
import time

logger = logging.getLogger(__name__)

class RetryStrategy:
    def __init__(self, max_retries=3, base_delay=2, max_delay=600):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def calculate_delay(self, attempt):
        '''Calculate exponential backoff with jitter'''
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter

    def should_retry(self, exception):
        '''Determine if exception should be retried'''
        # Don't retry on validation errors
        if isinstance(exception, ValueError):
            return False
        return True

def enqueue_with_retry(queue, func, *args, **kwargs):
    '''Enqueue job with automatic retry on failure'''
    job = queue.enqueue(
        func,
        *args,
        job_timeout='1h',
        result_ttl=500,
        on_failure='handle_job_failure',
        **kwargs
    )
    return job

def handle_job_failure(job, connection, exc_type, exc_value, traceback):
    '''Handle job failure with retry logic'''
    max_retries = job.meta.get('retries', 0)
    current_retry = job.meta.get('current_retry', 0)

    if current_retry < max_retries:
        strategy = RetryStrategy()
        delay = strategy.calculate_delay(current_retry)

        logger.info(f'Job {job.id} failed, retrying in {delay}s (attempt {current_retry + 1}/{max_retries})')

        job.meta['current_retry'] = current_retry + 1
        job.save_meta()

        # Re-enqueue with delay
        from rq_scheduler import Scheduler
        scheduler = Scheduler(connection=connection)
        scheduler.schedule(
            scheduled_time=datetime.utcnow() + timedelta(seconds=delay),
            func=job.func_name,
            args=job.args,
            kwargs=job.kwargs
        )

def retry_until_success(queue, func, *args, timeout=3600, **kwargs):
    '''Retry job until success or timeout'''
    start_time = time.time()
    attempt = 0

    while time.time() - start_time < timeout:
        try:
            job = queue.enqueue(func, *args, **kwargs)
            result = job.result
            if result is not None:
                return result
        except Exception as e:
            logger.error(f'Attempt {attempt} failed: {e}')

        attempt += 1
        delay = 2 ** min(attempt, 5)  # Cap at 32 seconds
        time.sleep(delay)

    raise TimeoutError(f'Job did not complete within {timeout} seconds')
"""

    def generate_bull_retry(self) -> str:
        """Generate Bull retry strategies"""
        return """
import Queue from 'bull';
import Redis from 'ioredis';

const redis = new Redis();
const jobQueue = new Queue('jobs', { redis });

class RetryStrategy {
    constructor(maxRetries = 3, baseDelay = 2000, maxDelay = 600000) {
        this.maxRetries = maxRetries;
        this.baseDelay = baseDelay;
        this.maxDelay = maxDelay;
    }

    calculateDelay(attempt) {
        const delay = Math.min(
            this.baseDelay * Math.pow(2, attempt),
            this.maxDelay
        );
        const jitter = Math.random() * delay * 0.1;
        return delay + jitter;
    }

    shouldRetry(error) {
        // Don't retry on validation errors
        if (error.message && error.message.includes('validation')) {
            return false;
        }
        return true;
    }
}

jobQueue.process(async (job) => {
    try {
        return await executeJob(job.data);
    } catch (error) {
        const strategy = new RetryStrategy();

        if (strategy.shouldRetry(error) && job.attemptsMade < strategy.maxRetries) {
            const delay = strategy.calculateDelay(job.attemptsMade);
            console.log(`Retrying job ${job.id} in ${delay}ms`);
            throw error; // Bull will handle retry
        }

        console.error(`Job ${job.id} failed after ${job.attemptsMade} attempts`);
        throw error;
    }
});

// Job failure handler with custom retry logic
jobQueue.on('failed', async (job, err) => {
    const maxRetries = 5;
    const strategy = new RetryStrategy();

    if (job.attemptsMade < maxRetries) {
        const delay = strategy.calculateDelay(job.attemptsMade);

        // Re-add job with delay
        const newJob = await jobQueue.add(job.data, {
            delay,
            priority: job.opts.priority,
            attempts: job.opts.attempts
        });

        console.log(`Job rescheduled with ID ${newJob.id}`);
    } else {
        console.error(`Job ${job.id} abandoned after ${maxRetries} retries`);
    }
});

export async function enqueueWithRetry(data, maxRetries = 3) {
    const job = await jobQueue.add(data, {
        attempts: maxRetries,
        backoff: {
            type: 'exponential',
            delay: 2000
        },
        removeOnComplete: true,
        removeOnFail: false
    });
    return job;
}

async function executeJob(data) {
    // TODO: Implement job logic
    return data;
}
"""


def generate_retry_handler(framework: str, language: str) -> Dict[str, str]:
    """
    Generate retry handler code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = RetryHandler(framework, language)
    output = {}

    if language == "python":
        output["retry_handler.py"] = generator.generate_celery_retry()
        output["retry_handler_rq.py"] = generator.generate_rq_retry()
    elif language == "javascript":
        output["retry_handler.js"] = generator.generate_bull_retry()

    return output
