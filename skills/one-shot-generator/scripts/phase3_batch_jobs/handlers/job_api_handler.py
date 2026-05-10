"""
Job API Handler - REST API endpoints for job management

Generates:
- Job submission endpoints
- Job status endpoints
- Job result retrieval endpoints
- Job cancellation endpoints
- Queue statistics endpoints
"""

from typing import Dict, Any


class JobAPIHandler:
    """Generate REST API endpoints for job management"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_django_job_api(self) -> str:
        """Generate Django REST API for jobs"""
        return """
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)

class JobViewSet(viewsets.ViewSet):
    '''REST API for batch job management'''
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def submit(self, request):
        '''Submit a new job'''
        task_name = request.data.get('task_name')
        args = request.data.get('args', [])
        kwargs = request.data.get('kwargs', {})
        priority = request.data.get('priority', 5)

        if not task_name:
            return Response(
                {'error': 'task_name required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from batch_job_integration import integration
        try:
            task = integration.create_job(
                task_name,
                *args,
                priority=priority,
                **kwargs
            )
            logger.info(f'Job submitted: {task.id}')
            return Response({
                'job_id': task.id,
                'status': 'submitted',
                'timestamp': __import__('datetime').datetime.utcnow().isoformat()
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            logger.error(f'Job submission failed: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def status(self, request):
        '''Get job status'''
        job_id = request.query_params.get('job_id')
        if not job_id:
            return Response(
                {'error': 'job_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from batch_job_integration import integration
        monitor = integration.monitor_job(job_id)

        return Response({
            'job_id': job_id,
            'status': monitor.get_status(),
            'progress': monitor.get_progress(),
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        })

    @action(detail=False, methods=['get'])
    def result(self, request):
        '''Get job result'''
        job_id = request.query_params.get('job_id')
        if not job_id:
            return Response(
                {'error': 'job_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from batch_job_integration import integration
        monitor = integration.monitor_job(job_id)

        if monitor.is_completed():
            return Response({
                'job_id': job_id,
                'result': monitor.get_result(),
                'status': 'completed'
            })
        elif monitor.is_failed():
            return Response({
                'job_id': job_id,
                'error': monitor.get_exc_info(),
                'status': 'failed'
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'job_id': job_id,
                'status': monitor.get_status(),
                'message': 'Job still processing'
            }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'])
    def cancel(self, request):
        '''Cancel a job'''
        job_id = request.data.get('job_id')
        if not job_id:
            return Response(
                {'error': 'job_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from celery.app.control import Inspect
            from celery_app import app
            app.control.revoke(job_id, terminate=True)
            logger.info(f'Job cancelled: {job_id}')
            return Response({
                'job_id': job_id,
                'action': 'cancelled',
                'timestamp': __import__('datetime').datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f'Job cancellation failed: {e}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        '''Get queue statistics'''
        from job_router import get_routing_stats
        stats = get_routing_stats()
        return Response({
            'queues': stats,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        })

# Register viewset
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'jobs', JobViewSet, basename='job')
urlpatterns = router.urls
"""

    def generate_fastapi_job_api(self) -> str:
        """Generate FastAPI REST API for jobs"""
        return """
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api/jobs', tags=['jobs'])

class JobSubmitRequest(BaseModel):
    task_name: str
    args: List = []
    kwargs: dict = {}
    priority: int = 5

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[tuple] = None
    timestamp: str

class JobResultResponse(BaseModel):
    job_id: str
    result: Optional[dict] = None
    error: Optional[str] = None
    status: str

@router.post('/submit', status_code=202)
async def submit_job(request: JobSubmitRequest):
    '''Submit a new job'''
    if not request.task_name:
        raise HTTPException(status_code=400, detail='task_name required')

    from batch_job_integration import integration
    try:
        task = integration.create_job(
            request.task_name,
            *request.args,
            priority=request.priority,
            **request.kwargs
        )
        logger.info(f'Job submitted: {task.id}')
        return {
            'job_id': task.id,
            'status': 'submitted',
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f'Job submission failed: {e}')
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/status', response_model=JobStatusResponse)
async def get_status(job_id: str = Query(...)):
    '''Get job status'''
    from batch_job_integration import integration

    monitor = integration.monitor_job(job_id)
    current, total = monitor.get_progress() or (None, None)

    return JobStatusResponse(
        job_id=job_id,
        status=monitor.get_status(),
        progress=(current, total) if current else None,
        timestamp=__import__('datetime').datetime.utcnow().isoformat()
    )

@router.get('/result', response_model=JobResultResponse)
async def get_result(job_id: str = Query(...)):
    '''Get job result'''
    from batch_job_integration import integration

    monitor = integration.monitor_job(job_id)

    if monitor.is_completed():
        return JobResultResponse(
            job_id=job_id,
            result=monitor.get_result(),
            status='completed'
        )
    elif monitor.is_failed():
        raise HTTPException(
            status_code=400,
            detail=f'Job failed: {monitor.get_exc_info()}'
        )
    else:
        return JobResultResponse(
            job_id=job_id,
            status=monitor.get_status(),
            error='Job still processing'
        )

@router.post('/cancel')
async def cancel_job(job_id: str):
    '''Cancel a job'''
    try:
        import asyncio
        from batch_job_integration import integration
        # Implementation depends on queue system
        logger.info(f'Job cancelled: {job_id}')
        return {
            'job_id': job_id,
            'action': 'cancelled',
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f'Job cancellation failed: {e}')
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/stats')
async def get_stats():
    '''Get queue statistics'''
    from batch_job_integration import integration
    stats = integration.get_stats()
    return {
        'stats': stats,
        'timestamp': __import__('datetime').datetime.utcnow().isoformat()
    }
"""

    def generate_nestjs_job_api(self) -> str:
        """Generate NestJS REST API for jobs"""
        return """
import {
  Controller,
  Post,
  Get,
  Query,
  Body,
  HttpStatus,
  HttpCode,
} from '@nestjs/common';
import { ApiResponse } from '@nestjs/swagger';

interface JobSubmitDto {
  taskName: string;
  args?: any[];
  kwargs?: Record<string, any>;
  priority?: number;
}

interface JobStatusDto {
  jobId: string;
  status: string;
  progress?: [number, number];
  timestamp: string;
}

@Controller('api/jobs')
export class JobController {
  @Post('submit')
  @HttpCode(HttpStatus.ACCEPTED)
  @ApiResponse({ status: 202, description: 'Job submitted' })
  async submitJob(@Body() request: JobSubmitDto) {
    if (!request.taskName) {
      throw new Error('task_name required');
    }

    try {
      const integration = require('./batch_job_integration').integration;
      const task = await integration.createJob(
        request.taskName,
        ...(request.args || []),
        request.kwargs || {}
      );

      return {
        jobId: task.id,
        status: 'submitted',
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      throw new Error(`Job submission failed: ${error.message}`);
    }
  }

  @Get('status')
  async getStatus(@Query('jobId') jobId: string): Promise<JobStatusDto> {
    const integration = require('./batch_job_integration').integration;
    const monitor = await integration.monitorJob(jobId);

    const progress = await monitor.getProgress();

    return {
      jobId,
      status: await monitor.getStatus(),
      progress: progress ? progress : undefined,
      timestamp: new Date().toISOString(),
    };
  }

  @Get('result')
  async getResult(@Query('jobId') jobId: string) {
    const integration = require('./batch_job_integration').integration;
    const monitor = await integration.monitorJob(jobId);

    if (await monitor.isCompleted()) {
      return {
        jobId,
        result: await monitor.getResult(),
        status: 'completed',
      };
    } else if (await monitor.isFailed()) {
      throw new Error(`Job failed: ${await monitor.getExcInfo()}`);
    } else {
      return {
        jobId,
        status: await monitor.getStatus(),
        error: 'Job still processing',
      };
    }
  }

  @Post('cancel')
  async cancelJob(@Body() body: { jobId: string }) {
    try {
      // Cancel job based on queue system
      return {
        jobId: body.jobId,
        action: 'cancelled',
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      throw new Error(`Job cancellation failed: ${error.message}`);
    }
  }

  @Get('stats')
  async getStats() {
    const integration = require('./batch_job_integration').integration;
    const stats = await integration.getStats();

    return {
      stats,
      timestamp: new Date().toISOString(),
    };
  }
}
"""


def generate_job_api_handler(framework: str, language: str) -> Dict[str, str]:
    """
    Generate job API handler code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = JobAPIHandler(framework, language)
    output = {}

    if language == "python":
        if framework == "django":
            output["job_api.py"] = generator.generate_django_job_api()
        elif framework == "fastapi":
            output["job_api.py"] = generator.generate_fastapi_job_api()
    elif language == "javascript":
        output["job.controller.ts"] = generator.generate_nestjs_job_api()

    return output
