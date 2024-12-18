from flask import Flask, jsonify
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.semconv.resource import ResourceAttributes
import cProfile
import pstats
import io
import time
import tempfile
import json

# Create a resource identifying your application
resource = Resource.create({
    ResourceAttributes.SERVICE_NAME: "flask-app",
    ResourceAttributes.SERVICE_VERSION: "1.0.0",
})

# Initialize tracing
trace_provider = TracerProvider(resource=resource)
trace_processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True))
trace_provider.add_span_processor(trace_processor)
trace.set_tracer_provider(trace_provider)

# Initialize metrics
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="http://otel-collector:4317", insecure=True)
)
metric_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metric_provider)
meter = metrics.get_meter(__name__)

# Create metrics
function_duration = meter.create_histogram(
    name="function.duration",
    description="Duration of function execution",
    unit="ms",
)

function_calls = meter.create_counter(
    name="function.calls",
    description="Number of function calls",
)

# Create profile-specific metrics
profile_function_calls = meter.create_histogram(
    name="profile.function.calls",
    description="Number of calls per function",
    unit="calls",
)

profile_function_time = meter.create_histogram(
    name="profile.function.time",
    description="Time spent in each function",
    unit="ms",
)

profile_total_time = meter.create_histogram(
    name="profile.total.time",
    description="Total profiling time",
    unit="ms",
)

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

# Global profiler
profiler = cProfile.Profile()

def profile_function():
    """Function to simulate work and collect profiling data"""
    start_time = time.time()
    
    # Start profiling
    profiler.enable()
    
    # Do some work
    result = sum(range(1000000))
    time.sleep(0.1)  # Simulate I/O
    
    # Stop profiling
    profiler.disable()
    
    # Record metrics
    duration = (time.time() - start_time) * 1000  # Convert to ms
    function_duration.record(duration)
    function_calls.add(1)
    
    return result

def export_profile_stats(stats):
    """Export profile statistics as OpenTelemetry metrics"""
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("profile-stats-export") as span:
        # Add overall stats to span
        span.set_attribute("profile.total_calls", stats.total_calls)
        span.set_attribute("profile.total_time", stats.total_tt)
        
        # Process function stats
        for func, (cc, nc, tt, ct, callers) in stats.stats.items():
            # Extract function info
            if len(func) == 3:  # Normal case: (filename, line number, function name)
                filename, lineno, funcname = func
            else:
                filename, funcname = "unknown", str(func)
            
            # Record function-specific metrics
            attributes = {
                "function.name": funcname,
                "function.file": filename,
            }
            
            profile_function_calls.record(cc, attributes)  # Number of calls
            profile_function_time.record(tt * 1000, attributes)  # Time in ms
        
        # Record total time
        profile_total_time.record(stats.total_tt * 1000)

@app.route('/')
def hello():
    with trace.get_tracer(__name__).start_as_current_span("hello-operation") as span:
        result = profile_function()
        span.set_attribute("custom.attribute", "Hello World!")
        span.set_attribute("calculation.result", result)
        return "Hello World!"

@app.route('/profile')
def get_profile():
    with trace.get_tracer(__name__).start_as_current_span("profile-generation") as span:
        # Create a temporary file to store profile data
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            profiler.dump_stats(tmp.name)
            
            # Create string buffer for the stats output
            s = io.StringIO()
            
            # Create Stats object from the stats file
            stats = pstats.Stats(tmp.name, stream=s)
            stats.sort_stats('cumulative')
            stats.print_stats()
            
            # Export stats to OpenTelemetry
            export_profile_stats(stats)
            
            return jsonify({
                "profile_data": s.getvalue(),
                "total_calls": stats.total_calls,
                "total_time": stats.total_tt
            })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)