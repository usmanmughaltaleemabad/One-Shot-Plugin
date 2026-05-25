# Jaeger Setup Guide

This guide explains how to set up and run Jaeger locally for tracing the one-shot-prompting plugin pipeline.

## What is Jaeger?

Jaeger is an open-source tool for distributed tracing. It captures detailed traces of requests as they flow through your system, helping you understand performance bottlenecks and debug complex interactions.

## Prerequisites

- Docker and Docker Compose installed on your system

## Starting Jaeger

To start the Jaeger service locally:

```bash
docker-compose -f .docker/docker-compose.yml up -d
```

This command starts:
- **Jaeger All-in-One**: Combines the agent, collector, and query UI in a single container
- **Port 6831/UDP**: Jaeger agent port for receiving traces
- **Port 16686**: Jaeger UI dashboard (web interface)

## Accessing the Dashboard

Once Jaeger is running, open your browser and navigate to:

```
http://localhost:16686
```

You should see the Jaeger UI with a list of services in the dropdown menu.

## Expected Services

When the one-shot-prompting plugin generates features, traces will appear for:

- **one-shot-prompting**: Main plugin entry point
- **architect**: Specification generation and design stage
- **implementer**: Code generation stage
- **test-author**: Test generation stage
- **reviewer**: Security and quality review stage
- **critic**: Final validation and test execution stage
- **wirer**: Dependency injection and main.py wiring stage

Each service generates traces for all spans executed during feature generation.

## Viewing Traces

1. Select a service from the **Service** dropdown in the Jaeger UI
2. Click **Find Traces** to view all traces for that service
3. Click on a trace to view detailed span information
4. Use the timeline view to identify slow operations and bottlenecks

## Stopping Jaeger

To stop the Jaeger container:

```bash
docker-compose -f .docker/docker-compose.yml down
```

## Troubleshooting

### Connection Refused

If you see "connection refused" errors:
- Ensure Docker is running
- Check that port 16686 is not in use by another service
- Run `docker ps` to verify the jaeger container is running

### No Traces Appearing

If no traces appear in the dashboard:
- Verify the OTEL client in your code is configured to export to `localhost:6831`
- Check Docker logs: `docker logs <container-id>`
- Ensure the plugin is running and generating traces

## Configuration

The Jaeger service is configured via `.docker/docker-compose.yml`. Key settings:

- `COLLECTOR_ZIPKIN_HTTP_PORT`: HTTP port for Zipkin-compatible trace ingestion (9411)
- Ports are mapped to host machine for easy access during development

For advanced configuration, see [Jaeger Documentation](https://www.jaegertracing.io/docs/).
