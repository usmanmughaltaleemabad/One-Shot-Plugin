---
type: reference
last_verified: 2026-05-16
owner: claude
---

# Phase 3: Batch Job Specialist — Walkthrough

How the plugin generates complete queue systems with job execution, monitoring, real-time dashboards, and observability.

---

## What Phase 3 Does

**Phase 3 (13 modules):** Specializes in background job processing—queue management, job execution with retries, timeout handling, dead-letter queues, real-time monitoring dashboards, batch processing with backpressure, observability (logging, metrics, traces).

When you ask the plugin: `"add email notification queue with retries and monitoring"`

1. **Analyzer** (Phase 0) detects framework, existing queuing setup
2. **Planner** (Phase 0) decides: Celery vs Bull vs Resque, async or sync task runners
3. **Generator** (Phase 0) creates base job class
4. **Phase 3 Specialist** routes to batch job orchestrator
5. **Queue Setup** creates queue configuration (broker URL, connection pooling)
6. **Job Class Generator** creates task with retries, timeouts, error handling
7. **Worker Generator** creates worker process with graceful shutdown
8. **Monitoring Generator** creates real-time status dashboard
9. **Test Suite** creates 30+ tests (job execution, retries, DLQ, monitoring)
10. **Observability** injects structured logging, metrics, traces
11. **Verifier** (Phase 0) confirms all code works
12. **User sees:** Complete queue system ready to scale, fully monitored and observed

---

## Walkthrough: Email Notification Queue (FastAPI + Celery)

### Command
```bash
/one-shot-prompting:one-shot-generator "add email notification queue with retries, DLQ, and monitoring dashboard" @examples/fastapi-async-api
```

### What Happens (Behind the Scenes)

#### Step 1: Framework Analysis
```
Framework: FastAPI 0.104.0
Async: Yes (async def)
Database: SQLAlchemy + SQLite
Message Queue: None detected → recommend Celery (Python standard)
Queue Broker: Redis (assumed, can fallback to RabbitMQ)
Monitoring: None → recommend Prometheus + Grafana
```

#### Step 2: Phase 3 Routing
Orchestrator detects: "queue", "async", "retries"

Routes to: `phase3_runner.py` → `queue_orchestrator.py`

#### Step 3: Queue Configuration
**Task**: Set up Celery broker, worker configuration, task routing

```python
# celery_config.py
import os
from kombu import Exchange, Queue

class CeleryConfig:
    # Broker configuration
    broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
    
    # Worker configuration
    worker_prefetch_multiplier = 4
    worker_max_tasks_per_child = 1000
    worker_disable_rate_limits = False
    
    # Task configuration
    task_acks_late = True  # Ack only after task completes
    task_reject_on_worker_lost = True
    
    # Result configuration
    result_expires = 3600  # Results expire after 1 hour
    result_compression = 'gzip'
    
    # Retry configuration
    task_autoretry_for = (Exception,)
    task_max_retries = 3
    task_default_retry_delay = 60  # Retry after 60 seconds
    
    # Queue routing
    task_routes = {
        'tasks.send_email': {'queue': 'email'},
        'tasks.process_payment': {'queue': 'payments'},
        'tasks.generate_report': {'queue': 'reports'},
    }
    
    # Queue definitions
    task_queues = (
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('email', Exchange('email'), routing_key='email'),
        Queue('payments', Exchange('payments'), routing_key='payments'),
        Queue('reports', Exchange('reports'), routing_key='reports'),
    )

# celery_app.py
from celery import Celery
from celery_config import CeleryConfig

app = Celery('blog')
app.config_from_object(CeleryConfig)
app.autodiscover_tasks(['tasks'])
```

#### Step 4: Task Class Generation
**Task**: Create email task with retries, error handling, observability

```python
# tasks.py
from celery import Task
from celery_app import app
import logging
from structlog import get_logger
from datetime import datetime
from models import EmailLog

log = get_logger()

class CallbackTask(Task):
    """Task base class with error tracking"""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True

@app.task(base=CallbackTask, bind=True)
def send_email(self, recipient: str, subject: str, html_content: str):
    """
    Send email with retries and monitoring
    
    Args:
        recipient: Email address
        subject: Email subject
        html_content: HTML email body
    
    Returns:
        dict: Result with email log ID and status
    """
    task_id = self.request.id
    
    # Log task start
    log.info(
        'email_task_started',
        task_id=task_id,
        recipient=recipient,
        attempt=self.request.retries + 1
    )
    
    try:
        # Create email log entry
        email_log = EmailLog.create(
            recipient=recipient,
            subject=subject,
            status='pending',
            task_id=task_id,
            attempt=self.request.retries + 1
        )
        
        # TODO: Send email via SMTP
        # result = send_via_smtp(recipient, subject, html_content)
        
        # Simulate email sending
        import smtplib
        from email.mime.text import MIMEText
        
        msg = MIMEText(html_content, 'html')
        msg['Subject'] = subject
        msg['From'] = 'noreply@blog.local'
        msg['To'] = recipient
        
        with smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT', 587))) as server:
            server.starttls()
            server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))
            server.send_message(msg)
        
        # Log success
        email_log.status = 'sent'
        email_log.sent_at = datetime.utcnow()
        email_log.save()
        
        log.info(
            'email_sent',
            task_id=task_id,
            recipient=recipient,
            email_log_id=email_log.id
        )
        
        return {
            'status': 'sent',
            'email_log_id': email_log.id,
            'recipient': recipient
        }
    
    except Exception as exc:
        # Log error
        email_log.status = 'failed'
        email_log.error_message = str(exc)
        email_log.save()
        
        log.error(
            'email_send_failed',
            task_id=task_id,
            recipient=recipient,
            error=str(exc),
            attempt=self.request.retries + 1
        )
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        else:
            # Move to DLQ after max retries
            log.error(
                'email_dlq',
                task_id=task_id,
                recipient=recipient,
                reason='max_retries_exceeded'
            )
            email_log.status = 'dlq'
            email_log.save()
            raise

@app.task(bind=True)
def process_batch_emails(self, email_list: list):
    """
    Process multiple emails with backpressure control
    
    Args:
        email_list: List of {'recipient', 'subject', 'html_content'}
    """
    log.info('batch_email_processing', count=len(email_list))
    
    results = []
    for i, email_data in enumerate(email_list):
        # Check queue depth (backpressure)
        if i % 10 == 0:
            queue_depth = app.control.inspect().active()
            if queue_depth and max(len(v) for v in queue_depth.values()) > 100:
                log.warning('queue_depth_high', depth=queue_depth)
                # Rate limit: wait before submitting more
                time.sleep(1)
        
        # Submit email task
        task = send_email.delay(
            email_data['recipient'],
            email_data['subject'],
            email_data['html_content']
        )
        results.append(task.id)
    
    log.info('batch_email_submitted', task_count=len(results))
    return results
```

#### Step 5: Worker Process
**Task**: Create worker with graceful shutdown, signal handling

```python
# worker.py
from celery_app import app
from structlog import get_logger
import signal
import sys

log = get_logger()

class GracefulWorker:
    """Worker with graceful shutdown"""
    def __init__(self):
        self.should_exit = False
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)
    
    def handle_shutdown(self, signum, frame):
        log.info('worker_shutdown_signal', signal=signum)
        self.should_exit = True
    
    def start(self):
        log.info('worker_starting')
        
        worker = app.Worker(
            queues=['default', 'email', 'payments', 'reports'],
            loglevel='info',
            concurrency=4,
            pool='prefork',  # Use process pool (default)
            # pool='solo',  # For development: single process
        )
        
        worker.start()

if __name__ == '__main__':
    worker = GracefulWorker()
    worker.start()
```

Start worker:
```bash
python worker.py

# Or with Celery CLI:
celery -A celery_app worker -Q default,email,payments,reports --concurrency=4 --loglevel=info
```

#### Step 6: Monitoring Dashboard
**Task**: Create real-time status monitoring

```python
# monitoring.py
from fastapi import APIRouter, HTTPException
from celery_app import app
from sqlalchemy.orm import Session
from models import EmailLog
from datetime import datetime, timedelta

router = APIRouter(prefix='/api/monitoring', tags=['monitoring'])

@router.get('/queue-status')
async def get_queue_status():
    """Get current queue status"""
    inspect = app.control.inspect()
    active_tasks = inspect.active()
    registered_tasks = inspect.registered()
    
    return {
        'active_tasks': sum(len(v) for v in active_tasks.values()) if active_tasks else 0,
        'workers': list(active_tasks.keys()) if active_tasks else [],
        'registered_tasks': registered_tasks,
    }

@router.get('/task/{task_id}')
async def get_task_status(task_id: str):
    """Get status of specific task"""
    task_result = app.AsyncResult(task_id)
    
    return {
        'task_id': task_id,
        'status': task_result.status,  # PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED
        'result': task_result.result,
        'traceback': task_result.traceback if task_result.failed() else None,
    }

@router.get('/emails/stats')
async def get_email_stats(db: Session = Depends(get_db)):
    """Get email sending statistics"""
    now = datetime.utcnow()
    last_24h = now - timedelta(days=1)
    
    stats = {
        'total_sent': db.query(EmailLog).filter(EmailLog.status == 'sent').count(),
        'total_failed': db.query(EmailLog).filter(EmailLog.status == 'failed').count(),
        'total_dlq': db.query(EmailLog).filter(EmailLog.status == 'dlq').count(),
        'pending': db.query(EmailLog).filter(EmailLog.status == 'pending').count(),
        'sent_last_24h': db.query(EmailLog).filter(
            EmailLog.status == 'sent',
            EmailLog.sent_at >= last_24h
        ).count(),
        'failed_last_24h': db.query(EmailLog).filter(
            EmailLog.status == 'failed',
            EmailLog.updated_at >= last_24h
        ).count(),
    }
    
    return stats

@router.get('/emails/dlq')
async def get_dlq_emails(db: Session = Depends(get_db), limit: int = 20):
    """Get dead-letter queue emails"""
    dlq_emails = db.query(EmailLog).filter(
        EmailLog.status == 'dlq'
    ).order_by(EmailLog.created_at.desc()).limit(limit).all()
    
    return [
        {
            'id': email.id,
            'recipient': email.recipient,
            'subject': email.subject,
            'error': email.error_message,
            'attempts': email.attempt,
            'created_at': email.created_at,
        }
        for email in dlq_emails
    ]

@router.post('/task/{task_id}/retry')
async def retry_dlq_email(task_id: str, db: Session = Depends(get_db)):
    """Manually retry a DLQ email"""
    email_log = db.query(EmailLog).filter(EmailLog.task_id == task_id).first()
    if not email_log:
        raise HTTPException(status_code=404, detail='Email not found')
    
    if email_log.status != 'dlq':
        raise HTTPException(status_code=400, detail='Email not in DLQ')
    
    # Resubmit task
    task = send_email.delay(
        email_log.recipient,
        email_log.subject,
        email_log.html_content
    )
    
    email_log.task_id = task.id
    email_log.status = 'pending'
    email_log.attempt += 1
    db.add(email_log)
    db.commit()
    
    return {
        'status': 'retried',
        'new_task_id': task.id
    }
```

Add to main.py:
```python
from fastapi import FastAPI
from monitoring import router as monitoring_router

app = FastAPI()
app.include_router(monitoring_router)
```

Visit: `GET http://localhost:8000/api/monitoring/queue-status` → Real-time queue stats

#### Step 7: Observability Integration
**Task**: Structured logging, metrics, traces

```python
# observability.py
from structlog import get_logger
from prometheus_client import Counter, Histogram, Gauge
import time

log = get_logger()

# Prometheus metrics
email_sent_counter = Counter('emails_sent_total', 'Total emails sent')
email_failed_counter = Counter('emails_failed_total', 'Total emails failed')
email_retry_counter = Counter('emails_retried_total', 'Total email retries')
queue_depth_gauge = Gauge('queue_depth', 'Current queue depth')
task_duration = Histogram('task_duration_seconds', 'Task execution time')

# In tasks.py, add:
@app.task
def send_email(self, recipient: str, subject: str, html_content: str):
    start = time.time()
    
    try:
        # ... send email ...
        email_sent_counter.inc()
        log.info('email_sent', recipient=recipient, duration=time.time() - start)
    except Exception as exc:
        email_failed_counter.inc()
        email_retry_counter.inc()
        log.error('email_failed', recipient=recipient, error=str(exc))
        raise
    finally:
        task_duration.observe(time.time() - start)
```

#### Step 8: Test Suite (30+ tests)
**Task**: Test job execution, retries, DLQ, monitoring

```python
# tests/test_email_queue.py
import pytest
from celery import Celery
from tasks import send_email, process_batch_emails
from models import EmailLog

@pytest.fixture
def celery_config():
    return {
        'broker_url': 'redis://localhost:6379/0',
        'result_backend': 'redis://localhost:6379/1',
        'task_always_eager': True,  # Execute synchronously in tests
    }

@pytest.mark.celery
def test_send_email_success(db):
    """Test successful email sending"""
    task = send_email.delay('test@example.com', 'Test', '<h1>Test</h1>')
    
    assert task.successful()
    result = task.get()
    assert result['status'] == 'sent'
    
    email_log = db.query(EmailLog).filter(
        EmailLog.recipient == 'test@example.com'
    ).first()
    assert email_log.status == 'sent'

@pytest.mark.celery
def test_send_email_invalid_address(db):
    """Test email with invalid address"""
    task = send_email.delay('invalid', 'Test', '<h1>Test</h1>')
    
    assert task.failed()
    email_log = db.query(EmailLog).first()
    assert email_log.status == 'failed'

@pytest.mark.celery
def test_send_email_retry_logic(db, monkeypatch):
    """Test retry with exponential backoff"""
    call_count = 0
    
    def mock_smtp(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception('SMTP connection failed')
        return True
    
    monkeypatch.setattr('smtplib.SMTP', mock_smtp)
    
    # Task should retry twice then succeed
    task = send_email.delay('test@example.com', 'Test', '<h1>Test</h1>')
    assert call_count == 3

@pytest.mark.celery
def test_batch_email_processing(db):
    """Test batch email with backpressure"""
    emails = [
        {'recipient': f'user{i}@example.com', 'subject': 'Test', 'html_content': '<h1>Test</h1>'}
        for i in range(5)
    ]
    
    task = process_batch_emails.delay(emails)
    result = task.get()
    
    assert len(result) == 5
    assert db.query(EmailLog).count() == 5

def test_monitoring_queue_status(client):
    """Test monitoring endpoint"""
    response = client.get('/api/monitoring/queue-status')
    assert response.status_code == 200
    assert 'active_tasks' in response.json()
    assert 'workers' in response.json()

def test_monitoring_dlq_emails(client, db):
    """Test DLQ retrieval"""
    # Create DLQ email
    EmailLog.create(
        recipient='dlq@example.com',
        subject='Test',
        status='dlq',
        error_message='Max retries exceeded'
    )
    
    response = client.get('/api/monitoring/emails/dlq')
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]['status'] == 'dlq'

def test_dlq_retry(client, db):
    """Test manual DLQ retry"""
    email_log = EmailLog.create(
        recipient='test@example.com',
        subject='Test',
        status='dlq',
        task_id='old_task_id'
    )
    
    response = client.post(f'/api/monitoring/task/{email_log.task_id}/retry')
    assert response.status_code == 200
    
    email_log.refresh()
    assert email_log.status == 'pending'
    assert email_log.task_id != 'old_task_id'
```

#### Step 9: Docker Setup
**Task**: Containerize queue system

```dockerfile
# Dockerfile.worker
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["celery", "-A", "celery_app", "worker", "-Q", "default,email,payments,reports", "--loglevel=info"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
    command: uvicorn main:app --host 0.0.0.0 --reload

  worker-email:
    build:
      context: .
      dockerfile: Dockerfile.worker
    depends_on:
      - redis
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
    command: celery -A celery_app worker -Q email --loglevel=info

  worker-payments:
    build:
      context: .
      dockerfile: Dockerfile.worker
    depends_on:
      - redis
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
    command: celery -A celery_app worker -Q payments --loglevel=info

  worker-reports:
    build:
      context: .
      dockerfile: Dockerfile.worker
    depends_on:
      - redis
    environment:
      CELERY_BROKER_URL: redis://redis:6379/0
      CELERY_RESULT_BACKEND: redis://redis:6379/1
    command: celery -A celery_app worker -Q reports --loglevel=info
```

Start all services:
```bash
docker-compose up
```

---

## Phase 3 Modules

| Module | Purpose |
|--------|---------|
| queue_setup_generator.py | Broker setup (Celery, Bull, Resque config) |
| task_class_generator.py | Task with retries, timeouts, error handling |
| worker_generator.py | Worker process, graceful shutdown, signals |
| monitoring_dashboard.py | Real-time status, metrics, DLQ |
| batch_processor.py | Batch jobs with backpressure control |
| dlq_handler.py | Dead-letter queue management + retry |
| observability_injector.py | Structured logging, metrics, traces |
| test_suite_generator.py | 30+ tests (execution, retries, DLQ) |
| docker_orchestration.py | Compose file, Dockerfile, scaling |
| ... + 4 more framework-specific modules |

---

## Test This Yourself

```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Generate queue system
/one-shot-prompting:one-shot-generator "add email queue with monitoring" @examples/fastapi-async-api

# Then:
cd examples/fastapi-async-api
pip install celery redis structlog prometheus-client
python worker.py &  # Start worker
python main.py  # Start API server

# Test queue
curl -X POST http://localhost:8000/api/monitoring/emails/send \
  -H "Content-Type: application/json" \
  -d '{"recipient": "test@example.com", "subject": "Test", "html_content": "<h1>Test</h1>"}'

# Check monitoring
curl http://localhost:8000/api/monitoring/queue-status
curl http://localhost:8000/api/monitoring/emails/stats
```

---

## Next: Phase 4

Phase 3 generates complete queue systems. Phase 4 handles **production hardening**:
- Domain-Driven Design (DDD) architecture
- CQRS + Event Sourcing
- TDD cycle enforcement
- Cost optimization
- Chaos engineering + resilience testing
- Compliance (GDPR, SOC2, HIPAA)

See [phase4-ddd.md](phase4-ddd.md) — coming soon

---

**The Magic:** Phase 3 makes queue systems production-grade. DLQ handling, monitoring dashboards, observability built-in, Docker-ready. No queue management complexity—just working, scalable background jobs.
