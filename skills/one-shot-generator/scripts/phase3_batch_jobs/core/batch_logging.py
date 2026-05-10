"""
Batch Logging - Structured logging for batch jobs

Generates:
- Structured JSON logging
- Log aggregation setup
- Request tracking
- Performance logging
"""

from typing import Dict, Any


class BatchLogging:
    """Generate batch job logging code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_celery_logging(self) -> str:
        """Generate Celery structured logging"""
        return """
import logging
import json
from datetime import datetime
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
import time

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.setup_structured_logging()

    def setup_structured_logging(self):
        '''Configure JSON logging'''
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_task_start(self, task_id, task_name, args, kwargs):
        '''Log task start with context'''
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'task_start',
            'task_id': task_id,
            'task_name': task_name,
            'args_count': len(args),
            'kwargs_keys': list(kwargs.keys()),
        }
        self.logger.info(json.dumps(log_entry))

    def log_task_complete(self, task_id, task_name, duration, result=None):
        '''Log task completion'''
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'task_complete',
            'task_id': task_id,
            'task_name': task_name,
            'duration_seconds': duration,
            'result_type': type(result).__name__ if result else None,
        }
        self.logger.info(json.dumps(log_entry))

    def log_task_error(self, task_id, task_name, exception, traceback):
        '''Log task error'''
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'task_error',
            'task_id': task_id,
            'task_name': task_name,
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'traceback': traceback,
        }
        self.logger.error(json.dumps(log_entry))

    def log_metric(self, metric_name, value, tags=None):
        '''Log performance metric'''
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'metric',
            'metric_name': metric_name,
            'value': value,
            'tags': tags or {},
        }
        self.logger.info(json.dumps(log_entry))

logger = StructuredLogger('batch_jobs')

def setup_task_logging():
    '''Wire up task logging signals'''
    task_start_times = {}

    @task_prerun.connect
    def log_task_prerun(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
        task_start_times[task_id] = time.time()
        logger.log_task_start(task_id, task.name, args or (), kwargs or {})

    @task_postrun.connect
    def log_task_postrun(sender=None, task_id=None, task=None, retval=None, **extra):
        duration = time.time() - task_start_times.get(task_id, 0)
        logger.log_task_complete(task_id, task.name, duration, retval)

    @task_failure.connect
    def log_task_failure(sender=None, task_id=None, exception=None, traceback=None, **extra):
        logger.log_task_error(task_id, sender.name, exception, traceback)

setup_task_logging()
"""

    def generate_rq_logging(self) -> str:
        """Generate RQ structured logging"""
        return """
import logging
import json
from datetime import datetime
import time

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_job_enqueue(self, job_id, func_name, args, kwargs):
        '''Log job enqueue'''
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'job_enqueue',
            'job_id': job_id,
            'func_name': func_name,
            'args_count': len(args),
            'kwargs_keys': list(kwargs.keys()),
        }
        self.logger.info(json.dumps(log_entry))

    def log_job_start(self, job_id, func_name):
        '''Log job start execution'''
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'job_start',
            'job_id': job_id,
            'func_name': func_name,
        }
        self.logger.info(json.dumps(log_entry))

    def log_job_complete(self, job_id, func_name, duration, result=None):
        '''Log job completion'''
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'job_complete',
            'job_id': job_id,
            'func_name': func_name,
            'duration_seconds': duration,
            'result_type': type(result).__name__ if result else None,
        }
        self.logger.info(json.dumps(log_entry))

    def log_job_error(self, job_id, func_name, exception_type, exception_msg):
        '''Log job error'''
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event': 'job_error',
            'job_id': job_id,
            'func_name': func_name,
            'exception_type': exception_type,
            'exception_message': exception_msg,
        }
        self.logger.error(json.dumps(log_entry))

logger = StructuredLogger('rq_jobs')

def wrap_job_with_logging(func):
    '''Wrapper to add logging to any job function'''
    def wrapped(*args, **kwargs):
        job_id = kwargs.pop('__job_id__', 'unknown')
        start_time = time.time()

        logger.log_job_start(job_id, func.__name__)

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.log_job_complete(job_id, func.__name__, duration, result)
            return result
        except Exception as e:
            logger.log_job_error(job_id, func.__name__, type(e).__name__, str(e))
            raise

    return wrapped
"""

    def generate_bull_logging(self) -> str:
        """Generate Bull structured logging"""
        return """
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

class StructuredLogger {
    constructor(name) {
        this.name = name;
        this.logDir = path.join(__dirname, 'logs');
        this.ensureLogDir();
    }

    ensureLogDir() {
        if (!fs.existsSync(this.logDir)) {
            fs.mkdirSync(this.logDir, { recursive: true });
        }
    }

    logJobEnqueue(jobId, jobName, data) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            event: 'job_enqueue',
            jobId,
            jobName,
            dataKeys: Object.keys(data || {})
        };
        this.writeLog(logEntry);
    }

    logJobStart(jobId, jobName) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            event: 'job_start',
            jobId,
            jobName
        };
        this.writeLog(logEntry);
    }

    logJobComplete(jobId, jobName, duration, result) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            event: 'job_complete',
            jobId,
            jobName,
            durationMs: duration,
            resultType: result ? typeof result : null
        };
        this.writeLog(logEntry);
    }

    logJobError(jobId, jobName, errorType, errorMsg) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            event: 'job_error',
            jobId,
            jobName,
            errorType,
            errorMessage: errorMsg
        };
        this.writeLog(logEntry);
    }

    logMetric(metricName, value, tags = {}) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            event: 'metric',
            metricName,
            value,
            tags
        };
        this.writeLog(logEntry);
    }

    writeLog(logEntry) {
        console.log(JSON.stringify(logEntry));

        const logFile = path.join(
            this.logDir,
            \`\${this.name}-\${new Date().toISOString().split('T')[0]}.log\`
        );

        fs.appendFileSync(
            logFile,
            JSON.stringify(logEntry) + '\\n'
        );
    }
}

export const logger = new StructuredLogger('bull-jobs');

export function wrapJobWithLogging(jobName, handler) {
    return async (job) => {
        const startTime = Date.now();
        logger.logJobStart(job.id, jobName);

        try {
            const result = await handler(job);
            const duration = Date.now() - startTime;
            logger.logJobComplete(job.id, jobName, duration, result);
            return result;
        } catch (error) {
            logger.logJobError(job.id, jobName, error.constructor.name, error.message);
            throw error;
        }
    };
}
"""


def generate_batch_logging(framework: str, language: str) -> Dict[str, str]:
    """
    Generate batch job logging code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = BatchLogging(framework, language)
    output = {}

    if language == "python":
        output["batch_logging.py"] = generator.generate_celery_logging()
        output["batch_logging_rq.py"] = generator.generate_rq_logging()
    elif language == "javascript":
        output["batch_logging.js"] = generator.generate_bull_logging()

    return output
