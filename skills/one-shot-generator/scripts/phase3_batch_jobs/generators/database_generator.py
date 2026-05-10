"""
Database Generator - Database model generation for batch jobs

Generates:
- ORM models
- Database schemas
- Migration scripts
- Query builders
"""

from typing import Dict, Any


class DatabaseGenerator:
    """Generate database code for batch jobs"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_django_models(self) -> str:
        """Generate Django ORM models"""
        return """
from django.db import models
import json

class BatchJob(models.Model):
    '''Model for tracking batch jobs'''
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    job_id = models.CharField(max_length=36, unique=True, primary_key=True)
    task_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.IntegerField(default=5)
    queue_name = models.CharField(max_length=100, default='default')

    # Payload
    args = models.JSONField(default=list)
    kwargs = models.JSONField(default=dict)

    # Results
    result = models.JSONField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Retries
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)

    # Metadata
    worker_id = models.CharField(max_length=100, null=True, blank=True)
    progress = models.JSONField(default=dict)  # {'current': 50, 'total': 100}

    class Meta:
        db_table = 'batch_jobs'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['task_name', 'status']),
            models.Index(fields=['queue_name', 'priority']),
        ]

    def __str__(self):
        return f'{self.task_name} - {self.status}'

    def mark_running(self):
        '''Mark job as running'''
        import django.utils.timezone
        self.status = 'running'
        self.started_at = django.utils.timezone.now()
        self.save(update_fields=['status', 'started_at'])

    def mark_completed(self, result):
        '''Mark job as completed'''
        import django.utils.timezone
        self.status = 'completed'
        self.result = result
        self.completed_at = django.utils.timezone.now()
        self.save(update_fields=['status', 'result', 'completed_at'])

    def mark_failed(self, error):
        '''Mark job as failed'''
        import django.utils.timezone
        self.status = 'failed'
        self.error = error
        self.completed_at = django.utils.timezone.now()
        self.save(update_fields=['status', 'error', 'completed_at'])

class JobWebhookLog(models.Model):
    '''Log webhook deliveries'''
    job = models.ForeignKey(BatchJob, on_delete=models.CASCADE)
    webhook_url = models.URLField()
    event = models.CharField(max_length=100)
    status_code = models.IntegerField(null=True)
    response = models.TextField(null=True)
    attempt = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'job_webhook_logs'

class JobNotificationLog(models.Model):
    '''Log notifications sent'''
    job = models.ForeignKey(BatchJob, on_delete=models.CASCADE)
    notifier_type = models.CharField(max_length=50)  # email, slack, etc.
    recipient = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'job_notification_logs'
"""

    def generate_sqlalchemy_models(self) -> str:
        """Generate SQLAlchemy models"""
        return """
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, ForeignKey, Index, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

Base = declarative_base()

class JobStatus(enum.Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class BatchJob(Base):
    '''Batch job model'''
    __tablename__ = 'batch_jobs'

    job_id = Column(String(36), primary_key=True)
    task_name = Column(String(255), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    priority = Column(Integer, default=5)
    queue_name = Column(String(100), default='default')

    # Payload
    args = Column(JSON, default=[])
    kwargs = Column(JSON, default={})

    # Results
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Retries
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Metadata
    worker_id = Column(String(100), nullable=True)
    progress = Column(JSON, default={})

    # Relationships
    webhook_logs = relationship('JobWebhookLog', back_populates='job', cascade='all, delete-orphan')
    notification_logs = relationship('JobNotificationLog', back_populates='job', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_task_status', 'task_name', 'status'),
        Index('idx_queue_priority', 'queue_name', 'priority'),
    )

class JobWebhookLog(Base):
    '''Webhook delivery log'''
    __tablename__ = 'job_webhook_logs'

    id = Column(Integer, primary_key=True)
    job_id = Column(String(36), ForeignKey('batch_jobs.job_id'))
    webhook_url = Column(String(255))
    event = Column(String(100))
    status_code = Column(Integer, nullable=True)
    response = Column(Text, nullable=True)
    attempt = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship('BatchJob', back_populates='webhook_logs')

class JobNotificationLog(Base):
    '''Notification log'''
    __tablename__ = 'job_notification_logs'

    id = Column(Integer, primary_key=True)
    job_id = Column(String(36), ForeignKey('batch_jobs.job_id'))
    notifier_type = Column(String(50))
    recipient = Column(String(255))
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship('BatchJob', back_populates='notification_logs')
"""

    def generate_typeorm_models(self) -> str:
        """Generate TypeORM models"""
        return """
import {
  Entity,
  PrimaryColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToMany,
  Index,
} from 'typeorm';

export enum JobStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

@Entity('batch_jobs')
@Index('idx_status_created', ['status', 'createdAt'])
@Index('idx_task_status', ['taskName', 'status'])
@Index('idx_queue_priority', ['queueName', 'priority'])
export class BatchJob {
  @PrimaryColumn('varchar', { length: 36 })
  jobId: string;

  @Column('varchar', { length: 255 })
  taskName: string;

  @Column('enum', { enum: JobStatus, default: JobStatus.PENDING })
  status: JobStatus;

  @Column('int', { default: 5 })
  priority: number;

  @Column('varchar', { length: 100, default: 'default' })
  queueName: string;

  // Payload
  @Column('json', { default: [] })
  args: any[];

  @Column('json', { default: {} })
  kwargs: Record<string, any>;

  // Results
  @Column('json', { nullable: true })
  result: any;

  @Column('text', { nullable: true })
  error: string;

  // Timing
  @CreateDateColumn()
  createdAt: Date;

  @Column('timestamp', { nullable: true })
  startedAt: Date;

  @Column('timestamp', { nullable: true })
  completedAt: Date;

  // Retries
  @Column('int', { default: 0 })
  retryCount: number;

  @Column('int', { default: 3 })
  maxRetries: number;

  // Metadata
  @Column('varchar', { length: 100, nullable: true })
  workerId: string;

  @Column('json', { default: {} })
  progress: Record<string, any>;

  // Relationships
  @OneToMany(() => JobWebhookLog, log => log.job, { cascade: true })
  webhookLogs: JobWebhookLog[];

  @OneToMany(() => JobNotificationLog, log => log.job, { cascade: true })
  notificationLogs: JobNotificationLog[];
}

@Entity('job_webhook_logs')
export class JobWebhookLog {
  @PrimaryColumn('int')
  id: number;

  @Column('varchar', { length: 36 })
  jobId: string;

  @Column('varchar', { length: 255 })
  webhookUrl: string;

  @Column('varchar', { length: 100 })
  event: string;

  @Column('int', { nullable: true })
  statusCode: number;

  @Column('text', { nullable: true })
  response: string;

  @Column('int', { default: 1 })
  attempt: number;

  @CreateDateColumn()
  createdAt: Date;
}

@Entity('job_notification_logs')
export class JobNotificationLog {
  @PrimaryColumn('int')
  id: number;

  @Column('varchar', { length: 36 })
  jobId: string;

  @Column('varchar', { length: 50 })
  notifierType: string;

  @Column('varchar', { length: 255 })
  recipient: string;

  @Column('varchar', { length: 50 })
  status: string;

  @CreateDateColumn()
  createdAt: Date;
}
"""


def generate_database_models(framework: str, language: str) -> Dict[str, str]:
    """
    Generate database models.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = DatabaseGenerator(framework, language)
    output = {}

    if language == "python":
        if framework == "django":
            output["models.py"] = generator.generate_django_models()
        elif framework == "fastapi":
            output["models.py"] = generator.generate_sqlalchemy_models()
    elif language == "javascript":
        output["entities.ts"] = generator.generate_typeorm_models()

    return output
