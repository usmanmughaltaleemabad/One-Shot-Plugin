"""
Result Handler - Job result storage and retrieval

Generates:
- Result persistence
- Result caching
- Result retrieval patterns
- State management
"""

from typing import Dict, Any


class ResultHandler:
    """Generate job result handling code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_celery_result_handler(self) -> str:
        """Generate Celery result handling"""
        return """
from celery_app import app
from celery.result import AsyncResult
import json
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

class ResultHandler:
    def __init__(self, task_id):
        self.task_id = task_id
        self.result = AsyncResult(task_id)

    def save_result(self, data, expires=None):
        '''Save job result with optional expiration'''
        backend = app.backend
        if expires is None:
            expires = timedelta(hours=24)
        backend.store_result(self.task_id, data, state='SUCCESS', expires=expires)

    def get_result(self, **kwargs):
        '''Get result with timeout'''
        return self.result.get(**kwargs)

    def forget_result(self):
        '''Remove result from backend'''
        self.result.forget()

    def mark_as_processed(self):
        '''Mark result as read/processed'''
        self.save_result({'processed': True})

    def store_partial_result(self, index, data):
        '''Store partial result for streaming jobs'''
        key = f'{self.task_id}:partial:{index}'
        app.backend.set(key, json.dumps(data), ex=3600)

    def get_partial_results(self):
        '''Retrieve all partial results'''
        backend = app.backend
        pattern = f'{self.task_id}:partial:*'
        keys = backend.conn.keys(pattern)
        results = {}
        for key in keys:
            value = backend.get(key)
            results[key] = json.loads(value)
        return results

def batch_get_results(task_ids):
    '''Get results for multiple tasks'''
    results = {}
    for task_id in task_ids:
        handler = ResultHandler(task_id)
        try:
            results[task_id] = handler.get_result(timeout=1)
        except Exception as e:
            results[task_id] = {'error': str(e)}
    return results

def cleanup_old_results(hours=24):
    '''Clean up expired results'''
    backend = app.backend
    pattern = '*'
    keys = backend.conn.keys(pattern)
    cleaned = 0
    for key in keys:
        ttl = backend.conn.ttl(key)
        if ttl == -1:  # No expiration
            backend.conn.expire(key, 3600 * hours)
            cleaned += 1
    logger.info(f'Cleaned up {cleaned} results')
"""

    def generate_rq_result_handler(self) -> str:
        """Generate RQ result handling"""
        return """
from rq import Queue
from rq.job import JobStatus
from redis import Redis
import json
import logging

logger = logging.getLogger(__name__)

class ResultHandler:
    def __init__(self, job_id):
        self.job_id = job_id
        self.redis_conn = Redis()
        self.job = self.redis_conn.get_job(job_id)

    def save_result(self, data, ttl=None):
        '''Save job result'''
        if self.job:
            self.job.result = data
            self.job.save_result()
            if ttl:
                self.redis_conn.expire(self.job.key, ttl)

    def get_result(self):
        '''Get job result'''
        return self.job.result if self.job else None

    def delete_result(self):
        '''Delete result from cache'''
        if self.job:
            self.redis_conn.delete(self.job.key)

    def store_metadata(self, metadata):
        '''Store job metadata'''
        if self.job:
            self.job.meta.update(metadata)
            self.job.save_meta()

    def get_metadata(self):
        '''Get job metadata'''
        return self.job.meta if self.job else {}

    def archive_result(self, archive_ttl=86400*30):
        '''Archive result for long-term storage'''
        archive_key = f'archive:{self.job_id}'
        result_data = {
            'result': self.get_result(),
            'metadata': self.get_metadata(),
            'status': self.job.get_status() if self.job else None
        }
        self.redis_conn.setex(archive_key, archive_ttl, json.dumps(result_data))

def batch_save_results(results_dict, ttl=None):
    '''Save multiple job results'''
    for job_id, result_data in results_dict.items():
        handler = ResultHandler(job_id)
        handler.save_result(result_data, ttl)

def get_result_stats():
    '''Get statistics about stored results'''
    redis_conn = Redis()
    stats = {
        'total_keys': redis_conn.dbsize(),
        'memory_usage': redis_conn.info('memory')['used_memory_human']
    }
    return stats
"""

    def generate_bull_result_handler(self) -> str:
        """Generate Bull result handling"""
        return """
import Queue from 'bull';
import Redis from 'ioredis';

const redis = new Redis();
const jobQueue = new Queue('jobs', { redis });

class ResultHandler {
    constructor(jobId) {
        this.jobId = jobId;
    }

    async saveResult(data, options = {}) {
        const job = await jobQueue.getJob(this.jobId);
        if (job) {
            job.returnvalue = data;
            await job.save();
            if (options.ttl) {
                await redis.expire(`bull:${job.name}:${this.jobId}`, options.ttl);
            }
        }
    }

    async getResult() {
        const job = await jobQueue.getJob(this.jobId);
        return job ? job.returnvalue : null;
    }

    async deleteResult() {
        const job = await jobQueue.getJob(this.jobId);
        if (job) {
            await job.remove();
        }
    }

    async storeMetadata(metadata) {
        const job = await jobQueue.getJob(this.jobId);
        if (job) {
            job.data = { ...job.data, ...metadata };
            await job.save();
        }
    }

    async getMetadata() {
        const job = await jobQueue.getJob(this.jobId);
        return job ? job.data : {};
    }

    async archiveResult(ttl = 2592000) {
        const archiveKey = `archive:${this.jobId}`;
        const result = await this.getResult();
        const metadata = await this.getMetadata();
        const archiveData = {
            result,
            metadata,
            archivedAt: new Date().toISOString()
        };
        await redis.setex(archiveKey, ttl, JSON.stringify(archiveData));
    }
}

export async function batchSaveResults(resultsMap, options = {}) {
    for (const [jobId, resultData] of Object.entries(resultsMap)) {
        const handler = new ResultHandler(jobId);
        await handler.saveResult(resultData, options);
    }
}

export async function getResultStats() {
    const info = await redis.info('stats');
    return {
        totalConnections: parseInt(info.total_connections_received),
        totalCommands: parseInt(info.total_commands_processed)
    };
}
"""


def generate_result_handler(framework: str, language: str) -> Dict[str, str]:
    """
    Generate result handler code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = ResultHandler(framework, language)
    output = {}

    if language == "python":
        output["result_handler.py"] = generator.generate_celery_result_handler()
        output["result_handler_rq.py"] = generator.generate_rq_result_handler()
    elif language == "javascript":
        output["result_handler.js"] = generator.generate_bull_result_handler()

    return output
