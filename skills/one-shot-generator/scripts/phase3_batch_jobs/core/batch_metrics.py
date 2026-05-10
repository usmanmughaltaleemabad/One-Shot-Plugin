"""
Batch Metrics - Metrics collection and monitoring for batch jobs

Generates:
- Prometheus metrics
- Grafana dashboard config
- Performance metrics
- Job statistics
"""

from typing import Dict, Any


class BatchMetrics:
    """Generate batch metrics code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_celery_metrics(self) -> str:
        """Generate Celery metrics collection"""
        return """
from prometheus_client import Counter, Histogram, Gauge
from celery.signals import task_prerun, task_postrun, task_failure
import time

# Define metrics
jobs_total = Counter(
    'celery_jobs_total',
    'Total number of jobs processed',
    ['task_name', 'status']
)

job_duration = Histogram(
    'celery_job_duration_seconds',
    'Job execution duration in seconds',
    ['task_name'],
    buckets=(1, 5, 10, 30, 60, 300, 600)
)

jobs_in_progress = Gauge(
    'celery_jobs_in_progress',
    'Number of jobs currently in progress',
    ['task_name']
)

job_errors_total = Counter(
    'celery_job_errors_total',
    'Total number of job errors',
    ['task_name', 'error_type']
)

queue_size = Gauge(
    'celery_queue_size',
    'Number of jobs in queue',
    ['queue_name']
)

class MetricsCollector:
    def __init__(self):
        self.job_start_times = {}

    def setup_metrics(self):
        '''Wire up metrics collection'''
        @task_prerun.connect
        def on_task_prerun(sender=None, task_id=None, task=None, **extra):
            self.job_start_times[task_id] = time.time()
            jobs_in_progress.labels(task_name=task.name).inc()

        @task_postrun.connect
        def on_task_postrun(sender=None, task_id=None, task=None, **extra):
            if task_id in self.job_start_times:
                duration = time.time() - self.job_start_times.pop(task_id)
                job_duration.labels(task_name=task.name).observe(duration)
                jobs_in_progress.labels(task_name=task.name).dec()
                jobs_total.labels(task_name=task.name, status='success').inc()

        @task_failure.connect
        def on_task_failure(sender=None, task_id=None, exception=None, **extra):
            jobs_in_progress.labels(task_name=sender.name).dec()
            job_errors_total.labels(
                task_name=sender.name,
                error_type=type(exception).__name__
            ).inc()
            jobs_total.labels(task_name=sender.name, status='failed').inc()

    def get_metrics_summary(self):
        '''Get current metrics summary'''
        from prometheus_client import CollectorRegistry
        from prometheus_client.exposition import generate_latest

        registry = CollectorRegistry()
        return generate_latest(registry).decode('utf-8')

metrics_collector = MetricsCollector()
metrics_collector.setup_metrics()

def export_metrics_handler(request):
    '''Export metrics for Prometheus scraping'''
    from prometheus_client import generate_latest
    return generate_latest()
"""

    def generate_rq_metrics(self) -> str:
        """Generate RQ metrics collection"""
        return """
from prometheus_client import Counter, Histogram, Gauge
from redis import Redis
import logging

logger = logging.getLogger(__name__)

# Define metrics
jobs_total = Counter(
    'rq_jobs_total',
    'Total RQ jobs processed',
    ['queue_name', 'status']
)

job_duration = Histogram(
    'rq_job_duration_seconds',
    'RQ job duration in seconds',
    ['queue_name'],
    buckets=(1, 5, 10, 30, 60, 300, 600)
)

job_failures_total = Counter(
    'rq_job_failures_total',
    'Total RQ job failures',
    ['queue_name', 'error_type']
)

queue_size = Gauge(
    'rq_queue_size',
    'Number of jobs in queue',
    ['queue_name']
)

active_jobs = Gauge(
    'rq_active_jobs',
    'Number of active jobs',
    ['queue_name']
)

class RQMetricsCollector:
    def __init__(self):
        self.redis_conn = Redis()

    def collect_queue_metrics(self, queue_names):
        '''Collect metrics for queues'''
        from rq import Queue

        for queue_name in queue_names:
            queue = Queue(queue_name, connection=self.redis_conn)
            queue_size.labels(queue_name=queue_name).set(len(queue.job_ids))

            # Count failed jobs
            failed_registry = queue.failed_job_registry
            active_jobs.labels(queue_name=queue_name).set(len(queue.get_job_ids()))

    def record_job_completion(self, queue_name, duration):
        '''Record successful job'''
        job_duration.labels(queue_name=queue_name).observe(duration)
        jobs_total.labels(queue_name=queue_name, status='success').inc()

    def record_job_failure(self, queue_name, error_type):
        '''Record failed job'''
        job_failures_total.labels(queue_name=queue_name, error_type=error_type).inc()
        jobs_total.labels(queue_name=queue_name, status='failed').inc()

    def get_metrics_summary(self):
        '''Get metrics summary'''
        from prometheus_client import generate_latest
        return generate_latest()

rq_metrics = RQMetricsCollector()

def export_rq_metrics():
    '''Export RQ metrics'''
    from prometheus_client import generate_latest
    rq_metrics.collect_queue_metrics(['default', 'high_priority', 'low_priority'])
    return generate_latest()
"""

    def generate_bull_metrics(self) -> str:
        """Generate Bull metrics collection"""
        return """
import Queue from 'bull';
import Redis from 'ioredis';
import client from 'prom-client';

const redis = new Redis();

// Metrics
const jobsTotal = new client.Counter({
    name: 'bull_jobs_total',
    help: 'Total Bull jobs processed',
    labelNames: ['queue_name', 'status']
});

const jobDuration = new client.Histogram({
    name: 'bull_job_duration_seconds',
    help: 'Bull job duration in seconds',
    labelNames: ['queue_name'],
    buckets: [1, 5, 10, 30, 60, 300, 600]
});

const jobFailures = new client.Counter({
    name: 'bull_job_failures_total',
    help: 'Total Bull job failures',
    labelNames: ['queue_name', 'error_type']
});

const queueSize = new client.Gauge({
    name: 'bull_queue_size',
    help: 'Number of jobs in queue',
    labelNames: ['queue_name']
});

export class BullMetricsCollector {
    constructor(queueNames = ['default']) {
        this.queueNames = queueNames;
        this.queues = {};
        this.startTimes = new Map();
    }

    async initialize() {
        for (const queueName of this.queueNames) {
            this.queues[queueName] = new Queue(queueName, { redis });

            this.queues[queueName].on('active', (job) => {
                this.startTimes.set(job.id, Date.now());
            });

            this.queues[queueName].on('completed', (job) => {
                const duration = (Date.now() - this.startTimes.get(job.id)) / 1000;
                jobDuration.labels(queueName).observe(duration);
                jobsTotal.labels(queueName, 'success').inc();
            });

            this.queues[queueName].on('failed', (job, error) => {
                jobFailures.labels(queueName, error.constructor.name).inc();
                jobsTotal.labels(queueName, 'failed').inc();
            });
        }
    }

    async collectQueueMetrics() {
        for (const [queueName, queue] of Object.entries(this.queues)) {
            const count = await queue.count();
            queueSize.labels(queueName).set(count);
        }
    }

    async getMetrics() {
        await this.collectQueueMetrics();
        return client.register.metrics();
    }
}

export async function generateMetricsResponse() {
    const collector = new BullMetricsCollector(['default', 'highPriority', 'lowPriority']);
    await collector.initialize();

    // Periodically collect metrics
    setInterval(() => collector.collectQueueMetrics(), 30000);

    return collector;
}
"""


def generate_batch_metrics(framework: str, language: str) -> Dict[str, str]:
    """
    Generate batch metrics code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = BatchMetrics(framework, language)
    output = {}

    if language == "python":
        output["batch_metrics.py"] = generator.generate_celery_metrics()
        output["batch_metrics_rq.py"] = generator.generate_rq_metrics()
    elif language == "javascript":
        output["batch_metrics.js"] = generator.generate_bull_metrics()

    return output
