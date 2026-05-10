"""
Job Monitor - Monitor job execution and health

Generates:
- Job status tracking
- Heartbeat/progress tracking
- Job health checks
- Execution timeout handling
"""

from typing import Dict, Any


class JobMonitor:
    """Generate job monitoring code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_celery_monitor(self) -> str:
        """Generate Celery job monitoring"""
        return """
from celery import states
from celery_app import app
import time
import logging

logger = logging.getLogger(__name__)

class JobMonitor:
    def __init__(self, task_id):
        self.task_id = task_id
        self.result = app.AsyncResult(task_id)

    def get_status(self):
        '''Get current job status'''
        return self.result.state

    def is_running(self):
        '''Check if job is currently running'''
        return self.result.state == states.STARTED

    def is_completed(self):
        '''Check if job completed successfully'''
        return self.result.state == states.SUCCESS

    def is_failed(self):
        '''Check if job failed'''
        return self.result.state == states.FAILURE

    def get_progress(self):
        '''Get job progress information'''
        if self.result.state == 'PROGRESS':
            return self.result.info.get('current', 0), self.result.info.get('total', 100)
        return None, None

    def get_result(self):
        '''Get job result'''
        return self.result.result

    def get_exc_info(self):
        '''Get exception info if job failed'''
        if self.is_failed():
            return self.result.info
        return None

    def wait_for_completion(self, timeout=None, poll_interval=1):
        '''Block until job completes'''
        start_time = time.time()
        while True:
            if self.is_completed() or self.is_failed():
                return self.get_result()
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f'Job {self.task_id} timed out')
            time.sleep(poll_interval)

def publish_job_heartbeat(task_id, progress=None):
    '''Publish job heartbeat'''
    logger.info(f'Job {task_id} heartbeat - progress: {progress}')

def check_job_health(task_id):
    '''Check job health and restart if needed'''
    monitor = JobMonitor(task_id)
    if monitor.is_failed():
        logger.error(f'Job {task_id} health check failed')
        return False
    return True

def watch_job_status(task_id, callback=None):
    '''Watch job status changes'''
    monitor = JobMonitor(task_id)
    while not (monitor.is_completed() or monitor.is_failed()):
        status = monitor.get_status()
        if callback:
            callback(task_id, status)
        time.sleep(1)
"""

    def generate_rq_monitor(self) -> str:
        """Generate RQ job monitoring"""
        return """
from rq.job import JobStatus
from redis import Redis
import time
import logging

logger = logging.getLogger(__name__)

class JobMonitor:
    def __init__(self, job_id):
        self.job_id = job_id
        self.redis_conn = Redis()
        self.job = self.redis_conn.get_job(job_id)

    def get_status(self):
        '''Get current job status'''
        return self.job.get_status()

    def is_running(self):
        '''Check if job is running'''
        return self.job.is_started

    def is_completed(self):
        '''Check if job completed'''
        return self.job.is_finished

    def is_failed(self):
        '''Check if job failed'''
        return self.job.is_failed

    def get_progress(self):
        '''Get job progress'''
        if hasattr(self.job, 'meta'):
            return self.job.meta.get('progress', None)
        return None

    def get_result(self):
        '''Get job result'''
        return self.job.result

    def get_exc_info(self):
        '''Get exception info'''
        return self.job.exc_info

    def wait_for_completion(self, timeout=None):
        '''Wait for job completion'''
        start_time = time.time()
        while True:
            if self.is_completed() or self.is_failed():
                return self.get_result()
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f'Job {self.job_id} timed out')
            time.sleep(1)

def record_job_progress(job, current, total):
    '''Record job progress'''
    job.meta['progress'] = {'current': current, 'total': total}
    job.save_meta()
"""

    def generate_bull_monitor(self) -> str:
        """Generate Bull job monitoring"""
        return """
import Queue from 'bull';
import Redis from 'ioredis';

const redis = new Redis();
const jobQueue = new Queue('jobs', { redis });

class JobMonitor {
    constructor(jobId) {
        this.jobId = jobId;
    }

    async getStatus() {
        const job = await jobQueue.getJob(this.jobId);
        return job ? await job.getState() : null;
    }

    async isRunning() {
        const state = await this.getStatus();
        return state === 'active';
    }

    async isCompleted() {
        const state = await this.getStatus();
        return state === 'completed';
    }

    async isFailed() {
        const state = await this.getStatus();
        return state === 'failed';
    }

    async getProgress() {
        const job = await jobQueue.getJob(this.jobId);
        return job ? job.progress() : null;
    }

    async getResult() {
        const job = await jobQueue.getJob(this.jobId);
        return job ? job.returnvalue : null;
    }

    async waitForCompletion(timeout = null) {
        const startTime = Date.now();
        while (true) {
            const isCompleted = await this.isCompleted();
            const isFailed = await this.isFailed();
            if (isCompleted || isFailed) {
                return await this.getResult();
            }
            if (timeout && Date.now() - startTime > timeout) {
                throw new Error(`Job ${this.jobId} timed out`);
            }
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
}

export async function watchJobProgress(jobId, onProgress) {
    const monitor = new JobMonitor(jobId);
    while (true) {
        const progress = await monitor.getProgress();
        if (onProgress) {
            onProgress(jobId, progress);
        }
        const isCompleted = await monitor.isCompleted();
        const isFailed = await monitor.isFailed();
        if (isCompleted || isFailed) {
            break;
        }
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
}
"""


def generate_job_monitor(framework: str, language: str) -> Dict[str, str]:
    """
    Generate job monitoring code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = JobMonitor(framework, language)
    output = {}

    if language == "python":
        output["job_monitor.py"] = generator.generate_celery_monitor()
        output["job_monitor_rq.py"] = generator.generate_rq_monitor()
    elif language == "javascript":
        output["job_monitor.js"] = generator.generate_bull_monitor()

    return output
