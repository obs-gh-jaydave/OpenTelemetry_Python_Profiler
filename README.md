# OpenTelemetry Python Profiler Demo

This project demonstrates how to integrate OpenTelemetry with Python Flask applications for distributed tracing, metrics collection, and CPU/memory profiling.

## Features

- Flask application with OpenTelemetry instrumentation
- Automated CPU and memory profiling
- Trace and metrics collection
- Integration with Observe.ai for telemetry visualization
- Custom profile data collection endpoints

## Prerequisites

- Docker and Docker Compose
- Python 3.10 or later (if running locally)
- OpenTelemetry Collector
- Observe.ai account and credentials

## Project Structure

```
.
├── app/
│   ├── Dockerfile          # Flask app container configuration
│   ├── main.py            # Main Flask application
│   └── requirements.txt    # Python dependencies
├── docker-compose.yaml     # Container orchestration
├── otel-collector-config.yaml  # OpenTelemetry collector configuration
└── .env                   # Environment variables (not in version control)
```

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create a `.env` file with your Observe.ai credentials:
```bash
OBSERVE_CUSTOMER="your-customer-id"
OBSERVE_TOKEN="your-token"
```

3. Build and run the containers:
```bash
docker compose up --build
```

## Usage

The application exposes several endpoints:

### Base Endpoint
```bash
curl http://localhost:8080/
```
Returns "Hello World!" and generates trace data with a simple computation.

### Profile Endpoint
```bash
curl http://localhost:8080/profile
```
Returns detailed profiling information including:
- Function call counts
- Execution times
- Memory usage statistics

## OpenTelemetry Integration

The application sends telemetry data to Observe.ai through the OpenTelemetry collector:

- **Traces**: Track request flow and function execution
- **Metrics**: Monitor function duration and call counts
- **Profile Data**: CPU and memory usage statistics

### Available Metrics

- `function.duration`: Execution time of monitored functions
- `function.calls`: Number of function invocations
- `profile.function.calls`: Call counts per function from profiler
- `profile.function.time`: Time spent in each function
- `profile.total.time`: Total profiling duration

## Environment Variables

- `OBSERVE_CUSTOMER`: Your Observe.ai customer ID
- `OBSERVE_TOKEN`: Your Observe.ai authentication token
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OpenTelemetry collector endpoint
- `OTEL_PYTHON_PROFILING_ENABLED`: Enable/disable profiling
- `PYTHONTRACEMALLOC`: Enable memory allocation tracking

## Development

To add new instrumentation:

1. Add OpenTelemetry instrumentation to your code:
```python
from opentelemetry import trace, metrics

# Create a tracer
tracer = trace.get_tracer(__name__)

# Use the tracer
with tracer.start_as_current_span("operation-name") as span:
    span.set_attribute("attribute-name", "value")
```

2. Add new metrics:
```python
meter = metrics.get_meter(__name__)
counter = meter.create_counter("counter-name")
counter.add(1)
```

## Monitoring

View your application's telemetry data in Observe:
1. Log into your Observe account
2. Navigate to the APM section
3. Look for traces, metrics, and profile data from your application
