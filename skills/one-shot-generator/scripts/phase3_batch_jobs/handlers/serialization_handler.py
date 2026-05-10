"""
Serialization Handler - Job payload serialization

Generates:
- JSON serialization
- Pickle serialization
- Protobuf serialization (future)
- Message pack serialization
- Custom type handlers
"""

from typing import Dict, Any


class SerializationHandler:
    """Generate serialization code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_python_serialization(self) -> str:
        """Generate Python serialization handlers"""
        return """
import json
import pickle
import base64
import logging
from typing import Any, Type

logger = logging.getLogger(__name__)

class JobSerializer:
    '''Serialize job payloads'''

    @staticmethod
    def serialize_json(obj: Any) -> str:
        '''Serialize to JSON'''
        try:
            return json.dumps(obj, default=str)
        except TypeError as e:
            logger.error(f'JSON serialization failed: {e}')
            raise

    @staticmethod
    def deserialize_json(data: str) -> Any:
        '''Deserialize from JSON'''
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f'JSON deserialization failed: {e}')
            raise

    @staticmethod
    def serialize_pickle(obj: Any) -> str:
        '''Serialize to pickle (base64 encoded)'''
        try:
            pickled = pickle.dumps(obj)
            return base64.b64encode(pickled).decode()
        except pickle.PicklingError as e:
            logger.error(f'Pickle serialization failed: {e}')
            raise

    @staticmethod
    def deserialize_pickle(data: str) -> Any:
        '''Deserialize from pickle'''
        try:
            pickled = base64.b64decode(data.encode())
            return pickle.loads(pickled)
        except Exception as e:
            logger.error(f'Pickle deserialization failed: {e}')
            raise

class TypeAdapter:
    '''Handle custom type serialization'''

    @staticmethod
    def adapt(obj: Any) -> Any:
        '''Adapt object for JSON serialization'''
        import datetime
        import decimal
        import uuid

        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return obj.total_seconds()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)

def serialize_job_payload(args: tuple, kwargs: dict, format: str = 'json') -> dict:
    '''Serialize job arguments and keyword arguments'''
    if format == 'json':
        adapted_args = [TypeAdapter.adapt(arg) for arg in args]
        adapted_kwargs = {k: TypeAdapter.adapt(v) for k, v in kwargs.items()}
        return {
            'args': JobSerializer.serialize_json(adapted_args),
            'kwargs': JobSerializer.serialize_json(adapted_kwargs),
            'format': 'json'
        }
    elif format == 'pickle':
        return {
            'args': JobSerializer.serialize_pickle(args),
            'kwargs': JobSerializer.serialize_pickle(kwargs),
            'format': 'pickle'
        }
    else:
        raise ValueError(f'Unknown format: {format}')

def deserialize_job_payload(serialized: dict) -> tuple:
    '''Deserialize job arguments and keyword arguments'''
    format = serialized.get('format', 'json')

    if format == 'json':
        args = JobSerializer.deserialize_json(serialized['args'])
        kwargs = JobSerializer.deserialize_json(serialized['kwargs'])
    elif format == 'pickle':
        args = JobSerializer.deserialize_pickle(serialized['args'])
        kwargs = JobSerializer.deserialize_pickle(serialized['kwargs'])
    else:
        raise ValueError(f'Unknown format: {format}')

    return tuple(args), kwargs
"""

    def generate_nestjs_serialization(self) -> str:
        """Generate NestJS serialization handlers"""
        return """
import * as msgpack from 'msgpack5';
import * as protobuf from 'protobufjs';

export class JobSerializer {
    private static msgpack = msgpack();

    static serializeJson(obj: any): string {
        try {
            return JSON.stringify(obj);
        } catch (error) {
            console.error('JSON serialization failed:', error);
            throw error;
        }
    }

    static deserializeJson(data: string): any {
        try {
            return JSON.parse(data);
        } catch (error) {
            console.error('JSON deserialization failed:', error);
            throw error;
        }
    }

    static serializeMessagePack(obj: any): Buffer {
        try {
            return this.msgpack.encode(obj);
        } catch (error) {
            console.error('MessagePack serialization failed:', error);
            throw error;
        }
    }

    static deserializeMessagePack(data: Buffer): any {
        try {
            return this.msgpack.decode(data);
        } catch (error) {
            console.error('MessagePack deserialization failed:', error);
            throw error;
        }
    }
}

export class TypeAdapter {
    static adapt(obj: any): any {
        if (obj === null || obj === undefined) {
            return obj;
        }

        if (obj instanceof Date) {
            return obj.toISOString();
        } else if (obj instanceof Map) {
            return Object.fromEntries(obj);
        } else if (obj instanceof Set) {
            return Array.from(obj);
        } else if (obj instanceof Buffer) {
            return obj.toString('base64');
        } else if (typeof obj === 'object') {
            const adapted: Record<string, any> = {};
            for (const [key, value] of Object.entries(obj)) {
                adapted[key] = this.adapt(value);
            }
            return adapted;
        }

        return obj;
    }
}

export function serializeJobPayload(
    args: any[],
    kwargs: Record<string, any>,
    format: 'json' | 'msgpack' = 'json'
): Record<string, any> {
    if (format === 'json') {
        const adaptedArgs = args.map(arg => TypeAdapter.adapt(arg));
        const adaptedKwargs = Object.entries(kwargs).reduce(
            (acc, [k, v]) => ({ ...acc, [k]: TypeAdapter.adapt(v) }),
            {}
        );

        return {
            args: JobSerializer.serializeJson(adaptedArgs),
            kwargs: JobSerializer.serializeJson(adaptedKwargs),
            format: 'json',
        };
    } else if (format === 'msgpack') {
        return {
            args: JobSerializer.serializeMessagePack(args).toString('base64'),
            kwargs: JobSerializer.serializeMessagePack(kwargs).toString('base64'),
            format: 'msgpack',
        };
    } else {
        throw new Error(`Unknown format: ${format}`);
    }
}

export function deserializeJobPayload(
    serialized: Record<string, any>
): [any[], Record<string, any>] {
    const format = serialized.format || 'json';

    if (format === 'json') {
        const args = JobSerializer.deserializeJson(serialized.args);
        const kwargs = JobSerializer.deserializeJson(serialized.kwargs);
        return [args, kwargs];
    } else if (format === 'msgpack') {
        const args = JobSerializer.deserializeMessagePack(
            Buffer.from(serialized.args, 'base64')
        );
        const kwargs = JobSerializer.deserializeMessagePack(
            Buffer.from(serialized.kwargs, 'base64')
        );
        return [args, kwargs];
    } else {
        throw new Error(`Unknown format: ${format}`);
    }
}
"""


def generate_serialization_handler(framework: str, language: str) -> Dict[str, str]:
    """
    Generate serialization handler code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = SerializationHandler(framework, language)
    output = {}

    if language == "python":
        output["serialization.py"] = generator.generate_python_serialization()
    elif language == "javascript":
        output["serialization.service.ts"] = generator.generate_nestjs_serialization()

    return output
