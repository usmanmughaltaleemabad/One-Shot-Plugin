"""
Worker Generator - Generate worker process code

Generates:
- Worker initialization
- Worker configuration
- Signal handling (graceful shutdown)
- Multi-process worker management
"""

from typing import Dict, Any


class WorkerGenerator:
    """Generate worker code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_celery_worker(self) -> str:
        """Generate Celery worker startup code"""
        return """
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from celery_app import app
import logging
import signal
import sys

logger = logging.getLogger(__name__)

class WorkerConfig:
    WORKER_CONCURRENCY = 4
    WORKER_POOL = 'prefork'  # or 'solo', 'threads', 'eventlet'
    WORKER_TIMEOUT = 3600  # 1 hour
    WORKER_MAX_TASKS_PER_CHILD = 1000
    WORKER_LOG_LEVEL = 'INFO'

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    '''Log task execution start'''
    logger.info(f'Task {task.name} ({task_id}) started')

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, **extra):
    '''Log task execution completion'''
    logger.info(f'Task {task.name} ({task_id}) completed')

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **extra):
    '''Log task failures'''
    logger.error(f'Task {task_id} failed: {exception}')

def start_worker(queues=None, concurrency=None):
    '''Start Celery worker'''
    if queues is None:
        queues = ['default', 'high_priority']

    if concurrency is None:
        concurrency = WorkerConfig.WORKER_CONCURRENCY

    worker = app.Worker(
        queues=queues,
        loglevel=WorkerConfig.WORKER_LOG_LEVEL,
        concurrency=concurrency,
        pool=WorkerConfig.WORKER_POOL,
        max_tasks_per_child=WorkerConfig.WORKER_MAX_TASKS_PER_CHILD,
        task_events=True,
        time_limit=WorkerConfig.WORKER_TIMEOUT,
    )

    logger.info(f'Starting Celery worker with {concurrency} concurrency')

    def signal_handler(sig, frame):
        logger.info('Received shutdown signal, gracefully stopping')
        worker.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    worker.start()

if __name__ == '__main__':
    start_worker()
"""

    def generate_rq_worker(self) -> str:
        """Generate RQ worker code"""
        return """
from rq import Worker, Queue, Connection
from rq.job import JobStatus
from redis import Redis
import logging
import signal
import sys

logger = logging.getLogger(__name__)

class WorkerConfig:
    WORKER_TIMEOUT = 3600
    WORKER_DEFAULT_RESULT_TTL = 500
    WORKER_FAILURE_TTL = 86400

def start_worker(queue_names=None, worker_count=1):
    '''Start RQ worker'''
    if queue_names is None:
        queue_names = ['default', 'high_priority']

    redis_conn = Redis()

    with Connection(redis_conn):
        queues = [Queue(name, connection=redis_conn) for name in queue_names]
        worker = Worker(
            queues,
            name=f'worker-{id(worker)}',
            default_result_ttl=WorkerConfig.WORKER_DEFAULT_RESULT_TTL,
            job_monitoring_interval=30,
            log_level='INFO',
        )

        logger.info(f'Starting RQ worker processing {queue_names}')

        def signal_handler(sig, frame):
            logger.info('Received shutdown signal')
            worker.request_stop(format_exc())
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            worker.work(burst=False, with_scheduler=False)
        except Exception as e:
            logger.error(f'Worker error: {e}')
            raise

def start_multiple_workers(queue_names=None, worker_count=4):
    '''Start multiple worker processes'''
    import multiprocessing

    if queue_names is None:
        queue_names = ['default']

    processes = []
    for i in range(worker_count):
        p = multiprocessing.Process(
            target=start_worker,
            args=(queue_names,),
            name=f'rq-worker-{i}'
        )
        p.start()
        processes.append(p)
        logger.info(f'Started worker process {i}')

    # Keep workers running
    for p in processes:
        p.join()

if __name__ == '__main__':
    import sys
    worker_count = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    start_multiple_workers(worker_count=worker_count)
"""

    def generate_bull_worker(self) -> str:
        """Generate Bull worker code"""
        return """
import Queue from 'bull';
import Redis from 'ioredis';
import os from 'os';

const redis = new Redis();

class WorkerConfig {
    static WORKER_CONCURRENCY = 4;
    static WORKER_TIMEOUT = 3600000; // 1 hour in ms
    static MAX_STALLED_COUNT = 2;
}

export class BullWorker {
    constructor(queueNames = ['default', 'highPriority']) {
        this.queueNames = queueNames;
        this.queues = {};
        this.isRunning = false;
    }

    async start() {
        logger.info('Starting Bull worker');

        for (const queueName of this.queueNames) {
            const queue = new Queue(queueName, { redis });

            queue.process(
                WorkerConfig.WORKER_CONCURRENCY,
                async (job) => {
                    console.log(`Processing job ${job.id} from ${queueName}`);
                    try {
                        return await this.executeJob(job);
                    } catch (error) {
                        console.error(`Job ${job.id} failed: ${error.message}`);
                        throw error;
                    }
                }
            );

            queue.on('completed', (job) => {
                console.log(`Job ${job.id} completed`);
            });

            queue.on('failed', (job, err) => {
                console.error(`Job ${job.id} failed: ${err.message}`);
            });

            queue.on('error', (error) => {
                console.error(`Queue error: ${error.message}`);
            });

            this.queues[queueName] = queue;
        }

        this.isRunning = true;
        console.log(`Worker started with ${this.queueNames.length} queues`);
    }

    async executeJob(job) {
        // Override in subclass
        return await job.data;
    }

    async stop() {
        console.log('Stopping Bull worker');
        for (const queue of Object.values(this.queues)) {
            await queue.close();
        }
        this.isRunning = false;
    }

    async getStats() {
        const stats = {};
        for (const [name, queue] of Object.entries(this.queues)) {
            const jobCounts = await queue.getJobCounts();
            stats[name] = jobCounts;
        }
        return stats;
    }
}

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('Received SIGINT, shutting down gracefully');
    if (worker) {
        await worker.stop();
        process.exit(0);
    }
});

process.on('SIGTERM', async () => {
    console.log('Received SIGTERM, shutting down gracefully');
    if (worker) {
        await worker.stop();
        process.exit(0);
    }
});

// Start worker
const worker = new BullWorker();
await worker.start();

// Periodic stats logging
setInterval(async () => {
    const stats = await worker.getStats();
    console.log('Worker stats:', stats);
}, 60000);
"""


def generate_worker_code(framework: str, language: str) -> Dict[str, str]:
    """
    Generate worker code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = WorkerGenerator(framework, language)
    output = {}

    if language == "python":
        output["worker.py"] = generator.generate_celery_worker()
        output["worker_rq.py"] = generator.generate_rq_worker()
    elif language == "javascript":
        output["worker.js"] = generator.generate_bull_worker()

    return output
