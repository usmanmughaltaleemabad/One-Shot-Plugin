"""
Job Router - Route jobs to appropriate queues based on priority, type, and load

Generates:
- Queue routing logic
- Priority-based routing
- Load-aware routing
- Queue selection strategies
"""

from typing import Dict, Any


class JobRouter:
    """Generate job routing code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_celery_router(self) -> str:
        """Generate Celery job routing"""
        return """
from celery import Celery
from celery_app import app
import logging

logger = logging.getLogger(__name__)

class JobRouter:
    # Queue definitions
    QUEUES = {
        'default': {'priority': 5, 'max_workers': 4},
        'high_priority': {'priority': 10, 'max_workers': 2},
        'low_priority': {'priority': 1, 'max_workers': 8},
        'long_running': {'priority': 5, 'max_workers': 2, 'timeout': 3600},
    }

    # Task routing rules
    TASK_ROUTING = {
        'send_email': 'default',
        'process_image': 'high_priority',
        'generate_report': 'long_running',
        'cleanup_task': 'low_priority',
    }

    @staticmethod
    def get_queue_for_task(task_name, priority=None, estimated_duration=None):
        '''Determine queue for task'''
        # Check explicit routing
        if task_name in JobRouter.TASK_ROUTING:
            queue = JobRouter.TASK_ROUTING[task_name]
        # Route by priority
        elif priority and priority >= 8:
            queue = 'high_priority'
        elif priority and priority <= 3:
            queue = 'low_priority'
        # Route by duration
        elif estimated_duration and estimated_duration > 300:
            queue = 'long_running'
        else:
            queue = 'default'

        logger.info(f'Task {task_name} routed to {queue}')
        return queue

    @staticmethod
    def get_queue_load(queue_name):
        '''Check queue load'''
        inspect = app.control.Inspect()
        active_tasks = inspect.active()

        if not active_tasks:
            return 0

        queue_tasks = [t for q, tasks in active_tasks.items()
                      if q.startswith(queue_name) for t in tasks]
        return len(queue_tasks)

    @staticmethod
    def route_with_load_balancing(task_name, *args, **kwargs):
        '''Route task to least loaded queue'''
        queues_to_check = ['default', 'high_priority', 'low_priority']
        loads = {q: JobRouter.get_queue_load(q) for q in queues_to_check}

        # Choose queue with lowest load
        best_queue = min(loads, key=loads.get)

        logger.info(f'Task {task_name} routed to {best_queue} (load: {loads[best_queue]})')

        return app.send_task(task_name, args=args, queue=best_queue, kwargs=kwargs)

def route_task(task_name, *args, priority=None, estimated_duration=None, **kwargs):
    '''Route task with smart queue selection'''
    queue = JobRouter.get_queue_for_task(
        task_name,
        priority=priority,
        estimated_duration=estimated_duration
    )

    task = app.send_task(
        task_name,
        args=args,
        queue=queue,
        kwargs=kwargs
    )

    return task

def get_routing_stats():
    '''Get statistics about job routing'''
    inspect = app.control.Inspect()
    stats = {
        'queues': JobRouter.QUEUES,
        'active_queues': list(inspect.active_queues()),
        'queue_loads': {q: JobRouter.get_queue_load(q) for q in JobRouter.QUEUES.keys()}
    }
    return stats
"""

    def generate_rq_router(self) -> str:
        """Generate RQ job routing"""
        return """
from rq import Queue
from redis import Redis
import logging

logger = logging.getLogger(__name__)

class JobRouter:
    QUEUES = {
        'default': 4,
        'high_priority': 2,
        'low_priority': 8,
        'long_running': 2,
    }

    TASK_ROUTING = {
        'send_email': 'default',
        'process_image': 'high_priority',
        'generate_report': 'long_running',
        'cleanup': 'low_priority',
    }

    @staticmethod
    def get_queue_for_task(task_name, priority=None, estimated_duration=None):
        '''Determine queue for task'''
        if task_name in JobRouter.TASK_ROUTING:
            return JobRouter.TASK_ROUTING[task_name]

        if priority and priority >= 8:
            return 'high_priority'
        elif priority and priority <= 3:
            return 'low_priority'
        elif estimated_duration and estimated_duration > 300:
            return 'long_running'

        return 'default'

    @staticmethod
    def get_queue_load(queue_name):
        '''Check queue job count'''
        redis_conn = Redis()
        queue = Queue(queue_name, connection=redis_conn)
        return len(queue.job_ids)

    @staticmethod
    def route_with_load_balancing(func, *args, **kwargs):
        '''Route to least loaded queue'''
        queues = list(JobRouter.QUEUES.keys())
        loads = {q: JobRouter.get_queue_load(q) for q in queues}

        best_queue = min(loads, key=loads.get)
        queue = Queue(best_queue, connection=Redis())

        logger.info(f'Task routed to {best_queue} (load: {loads[best_queue]})')
        return queue.enqueue(func, *args, **kwargs)

def enqueue_task(func, *args, priority=None, estimated_duration=None, **kwargs):
    '''Enqueue task with intelligent routing'''
    queue_name = JobRouter.get_queue_for_task(
        func.__name__,
        priority=priority,
        estimated_duration=estimated_duration
    )

    queue = Queue(queue_name, connection=Redis())
    job = queue.enqueue(func, *args, **kwargs)

    logger.info(f'Task {func.__name__} enqueued to {queue_name}')
    return job

def get_routing_stats():
    '''Get routing statistics'''
    stats = {}
    for queue_name, max_workers in JobRouter.QUEUES.items():
        stats[queue_name] = {
            'max_workers': max_workers,
            'current_jobs': JobRouter.get_queue_load(queue_name)
        }
    return stats
"""

    def generate_bull_router(self) -> str:
        """Generate Bull job routing"""
        return """
import Queue from 'bull';
import Redis from 'ioredis';

const redis = new Redis();

class JobRouter {
    static QUEUES = {
        default: { priority: 5, concurrency: 4 },
        highPriority: { priority: 10, concurrency: 2 },
        lowPriority: { priority: 1, concurrency: 8 },
        longRunning: { priority: 5, concurrency: 2 }
    };

    static TASK_ROUTING = {
        sendEmail: 'default',
        processImage: 'highPriority',
        generateReport: 'longRunning',
        cleanup: 'lowPriority'
    };

    static getQueueForTask(taskName, priority = null, estimatedDuration = null) {
        if (JobRouter.TASK_ROUTING[taskName]) {
            return JobRouter.TASK_ROUTING[taskName];
        }

        if (priority && priority >= 8) return 'highPriority';
        if (priority && priority <= 3) return 'lowPriority';
        if (estimatedDuration && estimatedDuration > 300000) return 'longRunning';

        return 'default';
    }

    static async getQueueLoad(queueName) {
        const queue = new Queue(queueName, { redis });
        const count = await queue.count();
        return count;
    }

    static async routeWithLoadBalancing(taskName, data) {
        const queueNames = Object.keys(JobRouter.QUEUES);
        const loads = {};

        for (const queueName of queueNames) {
            loads[queueName] = await JobRouter.getQueueLoad(queueName);
        }

        const bestQueue = Object.keys(loads).reduce((a, b) =>
            loads[a] < loads[b] ? a : b
        );

        const queue = new Queue(bestQueue, { redis });
        const job = await queue.add(taskName, data);

        console.log(`Task routed to ${bestQueue} (load: ${loads[bestQueue]})`);
        return job;
    }
}

export async function enqueueTask(taskName, data, options = {}) {
    const queueName = JobRouter.getQueueForTask(
        taskName,
        options.priority,
        options.estimatedDuration
    );

    const queue = new Queue(queueName, { redis });
    const job = await queue.add(taskName, data, {
        priority: options.priority || 5,
        attempts: options.attempts || 3
    });

    console.log(`Task ${taskName} enqueued to ${queueName}`);
    return job;
}

export async function getRoutingStats() {
    const stats = {};
    for (const [queueName, config] of Object.entries(JobRouter.QUEUES)) {
        stats[queueName] = {
            ...config,
            currentJobs: await JobRouter.getQueueLoad(queueName)
        };
    }
    return stats;
}
"""


def generate_job_router(framework: str, language: str) -> Dict[str, str]:
    """
    Generate job router code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = JobRouter(framework, language)
    output = {}

    if language == "python":
        output["job_router.py"] = generator.generate_celery_router()
        output["job_router_rq.py"] = generator.generate_rq_router()
    elif language == "javascript":
        output["job_router.js"] = generator.generate_bull_router()

    return output
