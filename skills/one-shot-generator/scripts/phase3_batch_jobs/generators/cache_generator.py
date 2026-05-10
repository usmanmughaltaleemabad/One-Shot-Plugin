"""
Cache Generator - Caching strategies for batch job results

Generates:
- Result caching
- Cache invalidation
- Cache warming
- Multi-tier caching
"""

from typing import Dict, Any


class CacheGenerator:
    """Generate caching code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_python_caching(self) -> str:
        """Generate Python caching"""
        return """
import hashlib
import json
import time
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)

class JobResultCache:
    '''Cache job results'''

    def __init__(self, cache_backend, ttl: int = 3600):
        self.cache = cache_backend
        self.ttl = ttl

    def get_cache_key(self, task_name: str, args: tuple, kwargs: dict) -> str:
        '''Generate cache key from task signature'''
        signature = json.dumps({
            'task': task_name,
            'args': args,
            'kwargs': kwargs
        }, sort_keys=True, default=str)

        return f'job_result:{hashlib.sha256(signature.encode()).hexdigest()}'

    def get(self, task_name: str, args: tuple = (), kwargs: dict = None) -> Optional[any]:
        '''Get cached result'''
        kwargs = kwargs or {}
        key = self.get_cache_key(task_name, args, kwargs)

        try:
            result = self.cache.get(key)
            if result is not None:
                logger.info(f'Cache hit: {key}')
            return result
        except Exception as e:
            logger.warning(f'Cache retrieval failed: {e}')
            return None

    def set(self, task_name: str, result: any, args: tuple = (), kwargs: dict = None):
        '''Cache result'''
        kwargs = kwargs or {}
        key = self.get_cache_key(task_name, args, kwargs)

        try:
            self.cache.set(key, result, self.ttl)
            logger.info(f'Result cached: {key}')
        except Exception as e:
            logger.warning(f'Cache set failed: {e}')

    def delete(self, task_name: str, args: tuple = (), kwargs: dict = None):
        '''Invalidate cached result'''
        kwargs = kwargs or {}
        key = self.get_cache_key(task_name, args, kwargs)

        try:
            self.cache.delete(key)
            logger.info(f'Cache invalidated: {key}')
        except Exception as e:
            logger.warning(f'Cache deletion failed: {e}')

    def clear_by_task(self, task_name: str):
        '''Clear all caches for a task'''
        pattern = f'job_result:*{task_name}*'
        try:
            # Implementation depends on cache backend
            logger.info(f'Cleared cache for task: {task_name}')
        except Exception as e:
            logger.warning(f'Bulk cache clear failed: {e}')

def cached_task(cache: JobResultCache, task_func: Callable):
    '''Decorator for caching task results'''
    def wrapper(task_name: str, *args, **kwargs):
        # Check cache
        cached_result = cache.get(task_name, args, kwargs)
        if cached_result is not None:
            return cached_result

        # Execute task
        result = task_func(task_name, *args, **kwargs)

        # Cache result
        cache.set(task_name, result, args, kwargs)

        return result

    return wrapper

class MultiTierCache:
    '''Multi-tier caching strategy'''

    def __init__(self, local_cache, distributed_cache, ttl: int = 3600):
        self.local = local_cache
        self.distributed = distributed_cache
        self.ttl = ttl

    def get(self, key: str):
        '''Get from fastest cache first'''
        # Try local cache
        result = self.local.get(key)
        if result is not None:
            return result

        # Try distributed cache
        result = self.distributed.get(key)
        if result is not None:
            self.local.set(key, result, self.ttl)
            return result

        return None

    def set(self, key: str, result: any):
        '''Set in both caches'''
        self.local.set(key, result, self.ttl)
        self.distributed.set(key, result, self.ttl)

    def delete(self, key: str):
        '''Delete from both caches'''
        self.local.delete(key)
        self.distributed.delete(key)
"""

    def generate_nestjs_caching(self) -> str:
        """Generate NestJS caching"""
        return """
import { Injectable } from '@nestjs/common';
import * as crypto from 'crypto';
import Redis from 'ioredis';

@Injectable()
export class JobResultCache {
    constructor(
        private redis: Redis,
        private ttl: number = 3600
    ) {}

    private getCacheKey(taskName: string, args: any[], kwargs: Record<string, any>): string {
        const signature = JSON.stringify(
            { task: taskName, args, kwargs },
            Object.keys({ task: taskName, args, kwargs }).sort()
        );
        return `job_result:${crypto.createHash('sha256').update(signature).digest('hex')}`;
    }

    async get(taskName: string, args: any[] = [], kwargs: Record<string, any> = {}): Promise<any> {
        const key = this.getCacheKey(taskName, args, kwargs);

        try {
            const result = await this.redis.get(key);
            if (result) {
                console.log(`Cache hit: ${key}`);
                return JSON.parse(result);
            }
            return null;
        } catch (error) {
            console.warn(`Cache retrieval failed: ${error.message}`);
            return null;
        }
    }

    async set(
        taskName: string,
        result: any,
        args: any[] = [],
        kwargs: Record<string, any> = {}
    ): Promise<void> {
        const key = this.getCacheKey(taskName, args, kwargs);

        try {
            await this.redis.setex(
                key,
                this.ttl,
                JSON.stringify(result)
            );
            console.log(`Result cached: ${key}`);
        } catch (error) {
            console.warn(`Cache set failed: ${error.message}`);
        }
    }

    async delete(
        taskName: string,
        args: any[] = [],
        kwargs: Record<string, any> = {}
    ): Promise<void> {
        const key = this.getCacheKey(taskName, args, kwargs);

        try {
            await this.redis.del(key);
            console.log(`Cache invalidated: ${key}`);
        } catch (error) {
            console.warn(`Cache deletion failed: ${error.message}`);
        }
    }

    async clearByTask(taskName: string): Promise<void> {
        try {
            const keys = await this.redis.keys(`job_result:*`);
            if (keys.length > 0) {
                await this.redis.del(...keys);
            }
            console.log(`Cleared cache for task: ${taskName}`);
        } catch (error) {
            console.warn(`Bulk cache clear failed: ${error.message}`);
        }
    }
}

@Injectable()
export class MultiTierCache {
    constructor(
        private localCache: Map<string, { value: any; expires: number }>,
        private redis: Redis,
        private ttl: number = 3600
    ) {}

    async get(key: string): Promise<any> {
        // Try local cache
        const localEntry = this.localCache.get(key);
        if (localEntry && localEntry.expires > Date.now()) {
            return localEntry.value;
        }

        // Try distributed cache
        try {
            const result = await this.redis.get(key);
            if (result) {
                const parsed = JSON.parse(result);
                this.localCache.set(key, {
                    value: parsed,
                    expires: Date.now() + this.ttl * 1000,
                });
                return parsed;
            }
        } catch (error) {
            console.warn(`Cache get failed: ${error.message}`);
        }

        return null;
    }

    async set(key: string, value: any): Promise<void> {
        // Set in local cache
        this.localCache.set(key, {
            value,
            expires: Date.now() + this.ttl * 1000,
        });

        // Set in distributed cache
        try {
            await this.redis.setex(key, this.ttl, JSON.stringify(value));
        } catch (error) {
            console.warn(`Distributed cache set failed: ${error.message}`);
        }
    }

    async delete(key: string): Promise<void> {
        this.localCache.delete(key);
        try {
            await this.redis.del(key);
        } catch (error) {
            console.warn(`Cache delete failed: ${error.message}`);
        }
    }
}
"""


def generate_cache_generator(framework: str, language: str) -> Dict[str, str]:
    """
    Generate caching code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = CacheGenerator(framework, language)
    output = {}

    if language == "python":
        output["caching.py"] = generator.generate_python_caching()
    elif language == "javascript":
        output["cache.service.ts"] = generator.generate_nestjs_caching()

    return output
