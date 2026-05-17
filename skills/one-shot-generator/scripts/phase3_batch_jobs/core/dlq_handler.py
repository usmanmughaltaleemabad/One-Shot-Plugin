"""
DLQ Handler - Dead Letter Queue management for failed jobs

Generates:
- Dead letter queue setup
- Failed job routing
- DLQ processing
- Failure analysis
"""

from typing import Dict, Any


class DLQHandler:
    """Generate dead letter queue code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_celery_dlq(self) -> str:
        """Generate Celery dead letter queue"""
        return """
from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded, Reject
import logging

logger = logging.getLogger(__name__)

class DLQManager:
    DLQ_QUEUE_NAME = 'dead_letter_queue'
    MAX_RETRY_ATTEMPTS = 5

    @staticmethod
    def send_to_dlq(task_id, exception, task_args, task_kwargs):
        '''Send failed task to dead letter queue'''
        from celery_app import app

        dlq_task = {
            'original_task_id': task_id,
            'exception': str(exception),
            'exception_type': type(exception).__name__,
            'args': task_args,
            'kwargs': task_kwargs,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
            'retry_count': 0
        }

        app.send_task(
            'tasks.process_dlq_message',
            args=(dlq_task,),
            queue=DLQManager.DLQ_QUEUE_NAME,
            priority=10  # High priority for DLQ processing
        )

        logger.error(f'Task {task_id} sent to DLQ: {exception}')

def process_dlq_message(dlq_message):
    '''Process messages from dead letter queue'''
    task_id = dlq_message['original_task_id']
    exception = dlq_message['exception']

    logger.info(f'Processing DLQ message for task {task_id}')

    if dlq_message['retry_count'] >= DLQManager.MAX_RETRY_ATTEMPTS:
        logger.error(f'Task {task_id} exceeded max DLQ retries')
        # Send to permanent failure storage
        store_failed_task(dlq_message)
        return

    dlq_message['retry_count'] += 1

    try:
        # Attempt to reprocess or analyze failure
        analyze_failure(dlq_message)
    except Exception as e:
        logger.error(f'Error processing DLQ message: {e}')
        # Re-queue for later processing
        from celery_app import app
        app.send_task(
            'tasks.process_dlq_message',
            args=(dlq_message,),
            queue=DLQManager.DLQ_QUEUE_NAME,
            countdown=3600  # Retry in 1 hour
        )

def analyze_failure(dlq_message):
    '''Analyze failure and determine action'''
    exception_type = dlq_message['exception_type']

    if exception_type == 'ConnectionError':
        logger.warning(f'Connection error: {dlq_message["exception"]}')
        # Could retry after connection is restored
    elif exception_type == 'TimeoutError':
        logger.warning(f'Timeout error: {dlq_message["exception"]}')
        # Could increase timeout and retry
    else:
        logger.error(f'Unhandled error: {dlq_message["exception"]}')

def store_failed_task(dlq_message):
    '''Store failed task for manual investigation'''
    import json
    from datetime import datetime

    filename = f'failed_tasks/{dlq_message["original_task_id"]}.json'
    with open(filename, 'w') as f:
        json.dump({
            **dlq_message,
            'stored_at': datetime.utcnow().isoformat()
        }, f, indent=2)

    logger.error(f'Failed task stored to {filename}')

def get_dlq_status():
    '''Get dead letter queue status'''
    from celery_app import app
    from celery.app.control import Inspect

    inspect = Inspect(app=app)
    queue_stats = inspect.active_queues()

    dlq_stats = {
        'queue_name': DLQManager.DLQ_QUEUE_NAME,
        'pending_messages': len(queue_stats.get(DLQManager.DLQ_QUEUE_NAME, []))
    }

    return dlq_stats
"""

    def generate_rq_dlq(self) -> str:
        """Generate RQ dead letter queue"""
        return """
from rq import Queue
from redis import Redis
import json
import logging

logger = logging.getLogger(__name__)

class DLQManager:
    DLQ_QUEUE_NAME = 'dead_letter_queue'
    MAX_RETRY_ATTEMPTS = 5

    @staticmethod
    def send_to_dlq(job_id, exception, job_func, job_args, job_kwargs):
        '''Send failed job to dead letter queue'''
        redis_conn = Redis()
        dlq = Queue(DLQManager.DLQ_QUEUE_NAME, connection=redis_conn)

        dlq_job = {
            'original_job_id': job_id,
            'exception': str(exception),
            'exception_type': type(exception).__name__,
            'func': job_func,
            'args': job_args,
            'kwargs': job_kwargs,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
            'retry_count': 0
        }

        dlq.enqueue('process_dlq_job', dlq_job)
        logger.error(f'Job {job_id} sent to DLQ: {exception}')

def process_dlq_job(dlq_job):
    '''Process jobs from dead letter queue'''
    job_id = dlq_job['original_job_id']
    exception = dlq_job['exception']

    logger.info(f'Processing DLQ job {job_id}')

    if dlq_job['retry_count'] >= DLQManager.MAX_RETRY_ATTEMPTS:
        logger.error(f'Job {job_id} exceeded max DLQ retries')
        store_failed_job(dlq_job)
        return

    dlq_job['retry_count'] += 1

    try:
        analyze_failure(dlq_job)
    except Exception as e:
        logger.error(f'Error processing DLQ job: {e}')
        # Re-queue after delay
        from rq_scheduler import Scheduler
        scheduler = Scheduler(connection=Redis())
        from datetime import datetime, timedelta
        scheduler.schedule(
            scheduled_time=datetime.utcnow() + timedelta(hours=1),
            func='process_dlq_job',
            args=(dlq_job,)
        )

def analyze_failure(dlq_job):
    '''Analyze and log failure details'''
    logger.warning(f'Failure analysis: {dlq_job["exception_type"]} - {dlq_job["exception"]}')
    # Additional analysis logic here

def store_failed_job(dlq_job):
    '''Permanently store failed job'''
    redis_conn = Redis()
    key = f'failed_job:{dlq_job["original_job_id"]}'
    redis_conn.setex(key, 86400*30, json.dumps(dlq_job))
    logger.error(f'Failed job {dlq_job["original_job_id"]} archived')

def get_dlq_stats():
    '''Get dead letter queue statistics'''
    redis_conn = Redis()
    dlq = Queue(DLQManager.DLQ_QUEUE_NAME, connection=redis_conn)

    return {
        'queue_name': DLQManager.DLQ_QUEUE_NAME,
        'job_count': len(dlq.job_ids),
        'failed_jobs_archived': len(redis_conn.keys('failed_job:*'))
    }
"""

    def generate_bull_dlq(self) -> str:
        """Generate Bull dead letter queue"""
        return """
import Queue from 'bull';
import Redis from 'ioredis';

const redis = new Redis();
const dlqQueue = new Queue('dead_letter_queue', { redis });

class DLQManager {
    static DLQ_QUEUE_NAME = 'dead_letter_queue';
    static MAX_RETRY_ATTEMPTS = 5;

    static async sendToDLQ(jobId, error, jobData) {
        const dlqJob = {
            originalJobId: jobId,
            exception: error.message,
            exceptionType: error.constructor.name,
            data: jobData,
            timestamp: new Date().toISOString(),
            retryCount: 0
        };

        const job = await dlqQueue.add(dlqJob, {
            priority: 10, // High priority
            attempts: 1,
            backoff: {
                type: 'exponential',
                delay: 2000
            }
        });

        console.error(`Job ${jobId} sent to DLQ`);
        return job;
    }
}

dlqQueue.process(async (job) => {
    const dlqJob = job.data;

    console.log(`Processing DLQ job ${dlqJob.originalJobId}`);

    if (dlqJob.retryCount >= DLQManager.MAX_RETRY_ATTEMPTS) {
        console.error(`Job ${dlqJob.originalJobId} exceeded max retries`);
        await storeFailedJob(dlqJob);
        return;
    }

    dlqJob.retryCount++;

    try {
        await analyzeFailure(dlqJob);
    } catch (error) {
        console.error(`Error processing DLQ job: ${error.message}`);
        throw error;
    }
});

async function analyzeFailure(dlqJob) {
    console.warn(`Analyzing failure: ${dlqJob.exceptionType} - ${dlqJob.exception}`);
    // Analysis logic here
}

async function storeFailedJob(dlqJob) {
    const archiveKey = `failed_job:${dlqJob.originalJobId}`;
    await redis.setex(archiveKey, 2592000, JSON.stringify(dlqJob)); // 30 days
    console.error(`Failed job ${dlqJob.originalJobId} archived`);
}

export async function getDLQStats() {
    const count = await dlqQueue.count();
    const failedCount = redis.keys('failed_job:*');

    return {
        queueName: DLQManager.DLQ_QUEUE_NAME,
        pendingJobs: count,
        archivedJobs: (await failedCount).length
    };
}
"""


def generate_dlq_handler(framework: str, language: str) -> Dict[str, str]:
    """
    Generate dead letter queue handler code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = DLQHandler(framework, language)
    output = {}

    if language == "python":
        output["dlq_handler.py"] = generator.generate_celery_dlq()
        output["dlq_handler_rq.py"] = generator.generate_rq_dlq()
    elif language == "javascript":
        output["dlq_handler.js"] = generator.generate_bull_dlq()

    return output
