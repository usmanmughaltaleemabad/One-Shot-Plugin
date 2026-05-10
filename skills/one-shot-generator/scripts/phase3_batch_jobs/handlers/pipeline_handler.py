"""
Pipeline Handler - Job pipelines and task chaining

Generates:
- Sequential task pipelines
- Parallel task execution
- Conditional task flow
- Error handling in pipelines
- Pipeline templates
"""

from typing import Dict, Any, List


class PipelineHandler:
    """Generate job pipeline code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_celery_pipelines(self) -> str:
        """Generate Celery task pipelines"""
        return """
from celery import chain, group, chord, signature
from celery_app import app
import logging

logger = logging.getLogger(__name__)

class TaskPipeline:
    '''Build and execute task pipelines'''

    @staticmethod
    def sequential(tasks: list) -> object:
        '''Execute tasks sequentially'''
        # tasks = [
        #     ('task1', (arg1,), {'kwarg': value}),
        #     ('task2', (arg2,), {}),
        # ]
        pipeline = chain(*[
            signature(task_name, args=args, kwargs=kwargs)
            for task_name, args, kwargs in tasks
        ])
        return pipeline

    @staticmethod
    def parallel(tasks: list) -> object:
        '''Execute tasks in parallel'''
        job_group = group(*[
            signature(task_name, args=args, kwargs=kwargs)
            for task_name, args, kwargs in tasks
        ])
        return job_group

    @staticmethod
    def map_reduce(task_name: str, data: list, reduce_task: str) -> object:
        '''Map-reduce pattern'''
        # Map: apply task to each item
        mapper = group(
            signature(task_name, args=(item,))
            for item in data
        )
        # Reduce: aggregate results
        reducer = signature(reduce_task)

        pipeline = chord(mapper)(reducer)
        return pipeline

    @staticmethod
    def conditional(condition_task: str, true_task: str, false_task: str) -> object:
        '''Conditional task execution'''
        def handle_condition(result):
            if result:
                return signature(true_task).apply_async()
            else:
                return signature(false_task).apply_async()

        return signature(condition_task).apply_async() | handle_condition

def execute_pipeline(pipeline: object) -> str:
    '''Execute a pipeline and return task ID'''
    result = pipeline.apply_async()
    logger.info(f'Pipeline started: {result.id}')
    return result.id

# Example pipelines
def data_processing_pipeline(data_source: str) -> str:
    '''Typical data processing pipeline'''
    pipeline = chain(
        signature('fetch_data', args=(data_source,)),
        signature('validate_data'),
        signature('transform_data'),
        signature('load_data'),
    )
    return execute_pipeline(pipeline)

def parallel_processing_pipeline(items: list) -> str:
    '''Process items in parallel then aggregate'''
    pipeline = chord(
        group(signature('process_item', args=(item,)) for item in items)
    )(signature('aggregate_results'))

    return execute_pipeline(pipeline)

def multi_step_extraction(urls: list) -> str:
    '''Extract, transform, aggregate from multiple sources'''
    # Fetch from multiple URLs in parallel
    # Transform each result
    # Aggregate into final report

    pipeline = chord(
        group(signature('fetch_data', args=(url,)) for url in urls)
    )(signature('transform_and_aggregate'))

    return execute_pipeline(pipeline)
"""

    def generate_fastapi_pipelines(self) -> str:
        """Generate FastAPI/RQ pipelines"""
        return """
from rq import Queue, Worker
from redis import Redis
import logging

logger = logging.getLogger(__name__)

class JobPipeline:
    '''Build and manage job pipelines'''

    def __init__(self, redis_conn=None):
        self.redis_conn = redis_conn or Redis()
        self.queue = Queue(connection=self.redis_conn)

    def sequential(self, tasks: list):
        '''Execute tasks sequentially'''
        # tasks = [
        #     ('task1', (arg1,)),
        #     ('task2', (arg2,)),
        # ]

        def run_pipeline():
            results = []
            for task_name, args in tasks:
                job = self.queue.enqueue(task_name, *args)
                result = job.result
                results.append(result)
                logger.info(f'Completed {task_name}')
            return results

        return self.queue.enqueue(run_pipeline)

    def parallel(self, tasks: list):
        '''Execute tasks in parallel'''
        jobs = []
        for task_name, args in tasks:
            job = self.queue.enqueue(task_name, *args)
            jobs.append(job)
            logger.info(f'Started {task_name}')

        return {job.id: job for job in jobs}

    def map_reduce(self, map_task: str, data: list, reduce_task: str):
        '''Map-reduce pattern'''
        # Map phase: apply task to each data item
        mapped_jobs = []
        for item in data:
            job = self.queue.enqueue(map_task, item)
            mapped_jobs.append(job)

        # Reduce phase: aggregate results
        def reduce_results():
            results = [job.result for job in mapped_jobs]
            return self.queue.enqueue(reduce_task, results).result

        return self.queue.enqueue(reduce_results)

    def conditional(self, condition_task: str, condition_args: tuple,
                   true_task: str, false_task: str):
        '''Conditional execution'''
        def run_conditional():
            condition_job = self.queue.enqueue(condition_task, *condition_args)
            condition_result = condition_job.result

            if condition_result:
                return self.queue.enqueue(true_task).result
            else:
                return self.queue.enqueue(false_task).result

        return self.queue.enqueue(run_conditional)

# Global pipeline
pipeline = JobPipeline()

def execute_workflow(workflow_func):
    '''Decorator to enqueue workflow'''
    def wrapper(*args, **kwargs):
        return pipeline.queue.enqueue(workflow_func, *args, **kwargs)
    return wrapper

@execute_workflow
def extract_transform_load(source_url: str):
    '''Example ETL workflow'''
    # Step 1: Extract
    extract_job = pipeline.queue.enqueue('extract_data', source_url)
    data = extract_job.result

    # Step 2: Transform
    transform_job = pipeline.queue.enqueue('transform_data', data)
    transformed = transform_job.result

    # Step 3: Load
    load_job = pipeline.queue.enqueue('load_data', transformed)
    return load_job.result
"""

    def generate_bull_pipelines(self) -> str:
        """Generate Bull job pipelines"""
        return """
import Queue from 'bull';
import Redis from 'ioredis';

const redis = new Redis();
const jobQueue = new Queue('pipelines', { redis });

export class JobPipeline {
    constructor() {
        this.queue = jobQueue;
    }

    async sequential(tasks: Array<[string, any[]]>): Promise<string> {
        // tasks = [
        //   ['task1', [arg1]],
        //   ['task2', [arg2]],
        // ]

        const job = await this.queue.add(
            'pipeline:sequential',
            { tasks },
            { attempts: 3 }
        );

        console.log(`Pipeline started: ${job.id}`);
        return job.id;
    }

    async parallel(tasks: Array<[string, any[]]>): Promise<Record<string, string>> {
        const jobMap: Record<string, string> = {};

        for (const [taskName, args] of tasks) {
            const job = await this.queue.add(taskName, args);
            jobMap[taskName] = job.id;
            console.log(`Started ${taskName}: ${job.id}`);
        }

        return jobMap;
    }

    async mapReduce(
        mapTask: string,
        data: any[],
        reduceTask: string
    ): Promise<string> {
        // Map phase
        const mappedJobs = await Promise.all(
            data.map(item =>
                this.queue.add(mapTask, item)
            )
        );

        // Reduce phase
        const job = await this.queue.add('pipeline:reduce', {
            jobs: mappedJobs.map(j => j.id),
            reduceTask,
        });

        return job.id;
    }

    async conditional(
        conditionTask: string,
        conditionArgs: any[],
        trueTask: string,
        falseTask: string
    ): Promise<string> {
        const job = await this.queue.add('pipeline:conditional', {
            conditionTask,
            conditionArgs,
            trueTask,
            falseTask,
        });

        return job.id;
    }
}

// Register pipeline processors
jobQueue.process('pipeline:sequential', async (job) => {
    const { tasks } = job.data;
    const results: any[] = [];

    for (const [taskName, args] of tasks) {
        const result = await jobQueue.getJob(taskName);
        results.push(result?.returnvalue);
        console.log(`Completed ${taskName}`);
    }

    return results;
});

jobQueue.process('pipeline:reduce', async (job) => {
    const { jobs, reduceTask } = job.data;
    const results = await Promise.all(
        jobs.map(jid => jobQueue.getJob(jid))
    ).then(jobs => jobs.map(j => j?.returnvalue));

    const reduceJob = await jobQueue.add(reduceTask, results);
    return reduceJob.returnvalue;
});

jobQueue.process('pipeline:conditional', async (job) => {
    const { conditionTask, conditionArgs, trueTask, falseTask } = job.data;

    const condJob = await jobQueue.add(conditionTask, conditionArgs);
    const condResult = condJob.returnvalue;

    const nextTask = condResult ? trueTask : falseTask;
    const nextJob = await jobQueue.add(nextTask, []);
    return nextJob.returnvalue;
});

export const pipeline = new JobPipeline();
"""


def generate_pipeline_handler(framework: str, language: str) -> Dict[str, str]:
    """
    Generate pipeline handler code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = PipelineHandler(framework, language)
    output = {}

    if language == "python":
        output["pipelines.py"] = generator.generate_celery_pipelines()
        output["pipelines_rq.py"] = generator.generate_fastapi_pipelines()
    elif language == "javascript":
        output["pipeline.service.ts"] = generator.generate_bull_pipelines()

    return output
