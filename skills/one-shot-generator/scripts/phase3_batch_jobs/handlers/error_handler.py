"""
Error Handler - Job error handling and response formatting

Generates:
- Custom exception classes
- Error response formatting
- Error recovery strategies
- Error logging
- Error context preservation
"""

from typing import Dict, Any


class ErrorHandler:
    """Generate error handling code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_python_error_handler(self) -> str:
        """Generate Python error handling"""
        return """
import logging
import traceback
from enum import Enum

logger = logging.getLogger(__name__)

class JobErrorType(Enum):
    '''Job error types'''
    VALIDATION_ERROR = 'validation_error'
    TIMEOUT_ERROR = 'timeout_error'
    RESOURCE_ERROR = 'resource_error'
    EXTERNAL_API_ERROR = 'external_api_error'
    DATABASE_ERROR = 'database_error'
    UNKNOWN_ERROR = 'unknown_error'

class JobException(Exception):
    '''Base exception for job errors'''

    def __init__(self, message: str, error_type: JobErrorType = JobErrorType.UNKNOWN_ERROR,
                 recoverable: bool = False, retry_after: int = None):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.recoverable = recoverable
        self.retry_after = retry_after
        self.traceback = traceback.format_exc()

    def to_dict(self) -> dict:
        '''Convert to dictionary'''
        return {
            'message': self.message,
            'type': self.error_type.value,
            'recoverable': self.recoverable,
            'retry_after': self.retry_after,
            'traceback': self.traceback if logger.isEnabledFor(logging.DEBUG) else None
        }

class ValidationError(JobException):
    '''Validation failed'''
    def __init__(self, message: str):
        super().__init__(message, JobErrorType.VALIDATION_ERROR, recoverable=False)

class TimeoutError(JobException):
    '''Job timeout'''
    def __init__(self, message: str, retry_after: int = 300):
        super().__init__(message, JobErrorType.TIMEOUT_ERROR, recoverable=True, retry_after=retry_after)

class ResourceError(JobException):
    '''Resource unavailable'''
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message, JobErrorType.RESOURCE_ERROR, recoverable=True, retry_after=retry_after)

class ExternalAPIError(JobException):
    '''External API failure'''
    def __init__(self, message: str, status_code: int = None, retry_after: int = 300):
        super().__init__(message, JobErrorType.EXTERNAL_API_ERROR, recoverable=True, retry_after=retry_after)
        self.status_code = status_code

class DatabaseError(JobException):
    '''Database operation failed'''
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message, JobErrorType.DATABASE_ERROR, recoverable=True, retry_after=retry_after)

class ErrorHandler:
    '''Handle and log job errors'''

    @staticmethod
    def handle_exception(job_id: str, exception: Exception) -> dict:
        '''Handle exception and return response'''
        if isinstance(exception, JobException):
            error_response = exception.to_dict()
        else:
            # Wrap unknown exceptions
            error_response = {
                'message': str(exception),
                'type': JobErrorType.UNKNOWN_ERROR.value,
                'recoverable': False,
                'traceback': traceback.format_exc()
            }

        logger.error(f'Job {job_id} error: {error_response}')
        return error_response

    @staticmethod
    def should_retry(exception: Exception) -> bool:
        '''Check if exception is recoverable'''
        if isinstance(exception, JobException):
            return exception.recoverable
        return False

    @staticmethod
    def get_retry_delay(exception: Exception) -> int:
        '''Get retry delay in seconds'''
        if isinstance(exception, JobException) and exception.retry_after:
            return exception.retry_after
        return 60  # Default 1 minute

    @staticmethod
    def log_error(job_id: str, exception: Exception, context: dict = None):
        '''Log error with full context'''
        error_data = {
            'job_id': job_id,
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'context': context or {},
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }

        logger.error(f'Job error: {error_data}')
        return error_data

def format_error_response(job_id: str, exception: Exception) -> dict:
    '''Format error for API response'''
    handler = ErrorHandler()
    error = handler.handle_exception(job_id, exception)

    return {
        'job_id': job_id,
        'status': 'failed',
        'error': error,
        'timestamp': __import__('datetime').datetime.utcnow().isoformat()
    }
"""

    def generate_fastapi_error_handler(self) -> str:
        """Generate FastAPI error handling"""
        return """
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from enum import Enum
import logging
import traceback

logger = logging.getLogger(__name__)

class JobErrorType(Enum):
    '''Job error types'''
    VALIDATION_ERROR = 'validation_error'
    TIMEOUT_ERROR = 'timeout_error'
    RESOURCE_ERROR = 'resource_error'
    EXTERNAL_API_ERROR = 'external_api_error'
    DATABASE_ERROR = 'database_error'
    UNKNOWN_ERROR = 'unknown_error'

class JobException(Exception):
    '''Base job exception'''

    def __init__(self, message: str, error_type: JobErrorType = JobErrorType.UNKNOWN_ERROR,
                 status_code: int = 400, recoverable: bool = False):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.recoverable = recoverable
        self.traceback = traceback.format_exc()

    def to_dict(self) -> dict:
        return {
            'message': self.message,
            'type': self.error_type.value,
            'recoverable': self.recoverable
        }

class ValidationError(JobException):
    def __init__(self, message: str):
        super().__init__(message, JobErrorType.VALIDATION_ERROR, 400, False)

class TimeoutError(JobException):
    def __init__(self, message: str):
        super().__init__(message, JobErrorType.TIMEOUT_ERROR, 504, True)

class ResourceError(JobException):
    def __init__(self, message: str):
        super().__init__(message, JobErrorType.RESOURCE_ERROR, 503, True)

class ExternalAPIError(JobException):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message, JobErrorType.EXTERNAL_API_ERROR, status_code, True)

class DatabaseError(JobException):
    def __init__(self, message: str):
        super().__init__(message, JobErrorType.DATABASE_ERROR, 503, True)

async def job_exception_handler(request, exc: JobException):
    '''Handle job exceptions'''
    logger.error(f'Job exception: {exc.message}')

    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': exc.to_dict(),
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }
    )

def format_error_response(job_id: str, exception: Exception) -> dict:
    '''Format error for response'''
    if isinstance(exception, JobException):
        status_code = exception.status_code
        error_info = exception.to_dict()
    else:
        status_code = 500
        error_info = {
            'message': str(exception),
            'type': JobErrorType.UNKNOWN_ERROR.value,
            'recoverable': False
        }

    return {
        'job_id': job_id,
        'status': 'failed',
        'error': error_info,
        'status_code': status_code,
        'timestamp': __import__('datetime').datetime.utcnow().isoformat()
    }
"""

    def generate_nestjs_error_handler(self) -> str:
        """Generate NestJS error handling"""
        return """
import { HttpException, HttpStatus } from '@nestjs/common';
import { Response } from 'express';

export enum JobErrorType {
    ValidationError = 'validation_error',
    TimeoutError = 'timeout_error',
    ResourceError = 'resource_error',
    ExternalAPIError = 'external_api_error',
    DatabaseError = 'database_error',
    UnknownError = 'unknown_error',
}

export class JobException extends HttpException {
    constructor(
        message: string,
        statusCode: HttpStatus,
        public errorType: JobErrorType = JobErrorType.UnknownError,
        public recoverable: boolean = false
    ) {
        super(message, statusCode);
    }

    toJSON() {
        return {
            message: this.message,
            type: this.errorType,
            recoverable: this.recoverable,
        };
    }
}

export class ValidationError extends JobException {
    constructor(message: string) {
        super(message, HttpStatus.BAD_REQUEST, JobErrorType.ValidationError, false);
    }
}

export class TimeoutError extends JobException {
    constructor(message: string) {
        super(message, HttpStatus.GATEWAY_TIMEOUT, JobErrorType.TimeoutError, true);
    }
}

export class ResourceError extends JobException {
    constructor(message: string) {
        super(message, HttpStatus.SERVICE_UNAVAILABLE, JobErrorType.ResourceError, true);
    }
}

export class ExternalAPIError extends JobException {
    constructor(message: string) {
        super(message, HttpStatus.BAD_GATEWAY, JobErrorType.ExternalAPIError, true);
    }
}

export class DatabaseError extends JobException {
    constructor(message: string) {
        super(message, HttpStatus.SERVICE_UNAVAILABLE, JobErrorType.DatabaseError, true);
    }
}

export class ErrorHandler {
    static handle(jobId: string, exception: Error | JobException): any {
        console.error(`Job ${jobId} error:`, exception);

        if (exception instanceof JobException) {
            return {
                jobId,
                status: 'failed',
                error: exception.toJSON(),
                timestamp: new Date().toISOString(),
                statusCode: (exception as any).getStatus(),
            };
        }

        return {
            jobId,
            status: 'failed',
            error: {
                message: exception.message,
                type: JobErrorType.UnknownError,
                recoverable: false,
            },
            timestamp: new Date().toISOString(),
            statusCode: HttpStatus.INTERNAL_SERVER_ERROR,
        };
    }

    static shouldRetry(exception: Error | JobException): boolean {
        if (exception instanceof JobException) {
            return exception.recoverable;
        }
        return false;
    }
}

export function formatErrorResponse(
    jobId: string,
    exception: Error | JobException
): Record<string, any> {
    return ErrorHandler.handle(jobId, exception);
}
"""


def generate_error_handler(framework: str, language: str) -> Dict[str, str]:
    """
    Generate error handler code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = ErrorHandler(framework, language)
    output = {}

    if language == "python":
        output["error_handler.py"] = generator.generate_python_error_handler()
    elif language == "javascript":
        output["error.handler.ts"] = generator.generate_nestjs_error_handler()

    return output
