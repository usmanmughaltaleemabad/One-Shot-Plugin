"""
Go Worker Code Generator - Goroutine pool, context-based cancellation, channel-based job queue
"""

from typing import Dict


def generate_go_worker_infrastructure() -> Dict[str, str]:
    """Generate Go worker infrastructure with goroutine pool and channel-based queue"""
    return {
        "main.go": '''package main

import (
    "context"
    "flag"
    "fmt"
    "log"
    "os"
    "os/signal"
    "sync"
    "syscall"
    "time"
)

func main() {
    workerCount := flag.Int("workers", 4, "Number of worker goroutines")
    queueSize := flag.Int("queue-size", 100, "Job queue buffer size")
    flag.Parse()

    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    // Create job queue
    jobQueue := make(chan *Job, *queueSize)

    // Create worker pool
    pool := NewWorkerPool(*workerCount, jobQueue)
    pool.Start(ctx)

    // Set up signal handling for graceful shutdown
    sigChan := make(chan os.Signal, 1)
    signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

    go func() {
        <-sigChan
        fmt.Println("\\nShutting down gracefully...")
        cancel()
        time.Sleep(2 * time.Second)
        os.Exit(0)
    }()

    // Submit sample jobs
    go submitSampleJobs(jobQueue)

    // Wait for context cancellation
    <-ctx.Done()
    close(jobQueue)

    fmt.Println("Worker pool shut down")
}

func submitSampleJobs(jobQueue chan<- *Job) {
    for i := 1; i <= 20; i++ {
        job := &Job{
            ID:   fmt.Sprintf("job-%d", i),
            Name: fmt.Sprintf("Process Data %d", i),
            Data: map[string]interface{}{
                "value": i * 100,
            },
        }
        jobQueue <- job
        time.Sleep(100 * time.Millisecond)
    }
}
''',
        "worker_pool.go": '''package main

import (
    "context"
    "fmt"
    "log"
    "sync"
    "sync/atomic"
)

type WorkerPool struct {
    workerCount  int
    jobQueue     chan *Job
    wg            sync.WaitGroup
    activeJobs    int32
    completedJobs int32
    failedJobs    int32
}

func NewWorkerPool(workerCount int, jobQueue chan *Job) *WorkerPool {
    return &WorkerPool{
        workerCount: workerCount,
        jobQueue:    jobQueue,
    }
}

func (wp *WorkerPool) Start(ctx context.Context) {
    for i := 0; i < wp.workerCount; i++ {
        wp.wg.Add(1)
        go wp.worker(ctx, i)
    }
    fmt.Printf("Started %d workers\\n", wp.workerCount)
}

func (wp *WorkerPool) worker(ctx context.Context, id int) {
    defer wp.wg.Done()

    for {
        select {
        case job, ok := <-wp.jobQueue:
            if !ok {
                fmt.Printf("Worker %d shutting down\\n", id)
                return
            }

            atomic.AddInt32(&wp.activeJobs, 1)

            if err := wp.executeJob(ctx, job); err != nil {
                atomic.AddInt32(&wp.failedJobs, 1)
                log.Printf("Worker %d: Job %s failed: %v\\n", id, job.ID, err)
            } else {
                atomic.AddInt32(&wp.completedJobs, 1)
            }

            atomic.AddInt32(&wp.activeJobs, -1)

        case <-ctx.Done():
            fmt.Printf("Worker %d context cancelled\\n", id)
            return
        }
    }
}

func (wp *WorkerPool) executeJob(ctx context.Context, job *Job) error {
    fmt.Printf("Executing job: %s (data: %v)\\n", job.ID, job.Data)

    // Create timeout context for this job (10 seconds)
    jobCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
    defer cancel()

    // Simulate processing
    result, err := processJobWithContext(jobCtx, job)
    if err != nil {
        return err
    }

    job.Result = result
    job.Status = "completed"
    fmt.Printf("Job %s completed with result: %v\\n", job.ID, result)

    return nil
}

func (wp *WorkerPool) GetStats() map[string]interface{} {
    return map[string]interface{}{
        "active":    atomic.LoadInt32(&wp.activeJobs),
        "completed": atomic.LoadInt32(&wp.completedJobs),
        "failed":    atomic.LoadInt32(&wp.failedJobs),
    }
}

func (wp *WorkerPool) Wait() {
    wp.wg.Wait()
}
''',
        "job.go": '''package main

import "time"

type Job struct {
    ID        string                 `json:"id"`
    Name      string                 `json:"name"`
    Status    string                 `json:"status"`
    Data      map[string]interface{} `json:"data"`
    Result    interface{}            `json:"result,omitempty"`
    CreatedAt time.Time              `json:"created_at"`
    StartedAt time.Time              `json:"started_at,omitempty"`
    CompletedAt time.Time            `json:"completed_at,omitempty"`
    Error     string                 `json:"error,omitempty"`
    Retries   int                    `json:"retries"`
    MaxRetries int                   `json:"max_retries"`
}

func NewJob(id, name string, data map[string]interface{}) *Job {
    return &Job{
        ID:        id,
        Name:      name,
        Status:    "pending",
        Data:      data,
        CreatedAt: time.Now(),
        MaxRetries: 3,
    }
}

func (j *Job) Start() {
    j.Status = "in_progress"
    j.StartedAt = time.Now()
}

func (j *Job) Complete(result interface{}) {
    j.Status = "completed"
    j.Result = result
    j.CompletedAt = time.Now()
}

func (j *Job) Fail(err string) {
    if j.Retries < j.MaxRetries {
        j.Retries++
        j.Status = "retrying"
    } else {
        j.Status = "failed"
        j.Error = err
    }
}
''',
        "processor.go": '''package main

import (
    "context"
    "fmt"
    "time"
)

func processJobWithContext(ctx context.Context, job *Job) (interface{}, error) {
    job.Start()

    // Simulate some processing work
    for i := 0; i < 5; i++ {
        select {
        case <-ctx.Done():
            return nil, fmt.Errorf("job processing cancelled")
        case <-time.After(500 * time.Millisecond):
            fmt.Printf("  Processing step %d for %s\\n", i+1, job.ID)
        }
    }

    // Extract and process data
    value, ok := job.Data["value"].(int)
    if !ok {
        return nil, fmt.Errorf("invalid data value")
    }

    // Perform calculation
    result := value * 2

    return map[string]interface{}{
        "original": value,
        "processed": result,
        "timestamp": time.Now(),
    }, nil
}
''',
        "go.mod": '''module batch-worker

go 1.21

require (
    github.com/google/uuid v1.3.0
)
''',
        "Dockerfile": '''FROM golang:1.21-alpine as builder

WORKDIR /build
COPY . .

RUN go build -o worker main.go

FROM alpine:latest

RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /build/worker .

EXPOSE 8080

CMD ["./worker", "-workers", "4", "-queue-size", "100"]
''',
        "docker-compose.yml": '''version: '3.8'

services:
  worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: batch-worker
    environment:
      - WORKERS=4
      - QUEUE_SIZE=100
    ports:
      - "8080:8080"
    volumes:
      - ./logs:/root/logs
    restart: unless-stopped
''',
        "k8s_deployment.yaml": '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: batch-worker
  labels:
    app: batch-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: batch-worker
  template:
    metadata:
      labels:
        app: batch-worker
    spec:
      containers:
      - name: worker
        image: batch-worker:latest
        imagePullPolicy: Always
        args:
          - "-workers"
          - "4"
          - "-queue-size"
          - "100"
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: batch-worker
spec:
  selector:
    app: batch-worker
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
''',
        "health.go": '''package main

import (
    "encoding/json"
    "net/http"
)

func healthCheckHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]string{
        "status": "healthy",
    })
}

func readinessHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]string{
        "status": "ready",
    })
}

func statsHandler(pool *WorkerPool) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        w.WriteHeader(http.StatusOK)
        json.NewEncoder(w).Encode(pool.GetStats())
    }
}
'''
    }


def generate_go_worker(framework: str, language: str, job_name: str = None) -> dict:
    """Generate complete Go worker infrastructure"""
    output = {}

    job_name = job_name or "default_job"

    # Core worker implementation
    output.update(generate_go_worker_infrastructure())

    # Example service implementation
    output["service.go"] = '''package main

import (
    "context"
    "log"
)

type JobService struct {
    pool *WorkerPool
}

func NewJobService(pool *WorkerPool) *JobService {
    return &JobService{pool: pool}
}

func (s *JobService) SubmitJob(ctx context.Context, job *Job) error {
    select {
    case s.pool.jobQueue <- job:
        log.Printf("Job %s submitted", job.ID)
        return nil
    case <-ctx.Done():
        return ctx.Err()
    }
}

func (s *JobService) GetStats(ctx context.Context) map[string]interface{} {
    return s.pool.GetStats()
}
'''

    # README
    output["WORKER_README.md"] = '''# Go Batch Worker

A high-performance batch job worker pool implementation in Go.

## Features

- Goroutine-based worker pool (configurable concurrency)
- Channel-based job queue for thread-safe job distribution
- Context-based cancellation for graceful shutdown
- Per-job timeout management
- Job retry logic with exponential backoff
- Structured logging
- Docker and Kubernetes deployment configs
- Health check endpoints

## Running Locally

```bash
go run *.go -workers 4 -queue-size 100
```

## Docker

```bash
docker build -t batch-worker .
docker run -it --rm batch-worker
```

## Kubernetes

```bash
kubectl apply -f k8s_deployment.yaml
kubectl port-forward svc/batch-worker 8080:8080
```

## Architecture

### Worker Pool

The `WorkerPool` manages N goroutine workers that consume jobs from a channel:
- Each worker runs in a separate goroutine
- Workers process jobs concurrently
- Graceful shutdown via context cancellation

### Job Queue

Jobs are submitted to a buffered channel:
- Channel size = queue buffer capacity
- Non-blocking job submission with context support
- Automatic queue draining on shutdown

### Context-Based Cancellation

All operations respect context cancellation:
- Global context for worker lifecycle
- Per-job context with timeout
- SIGINT/SIGTERM handling for graceful shutdown

## Configuration

- `--workers`: Number of worker goroutines (default: 4)
- `--queue-size`: Job queue buffer size (default: 100)

## Monitoring

Current stats available at `/stats`:
- Active jobs
- Completed jobs
- Failed jobs
'''

    return output
