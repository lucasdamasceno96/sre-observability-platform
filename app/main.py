import time
import random
from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OT_LPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Configure OpenTelemetry Tracing
provider = TracerProvider()
processor = BatchSpanProcessor(OT_LPSpanExporter(endpoint="http://jaeger:4317", insecure=True))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

app = FastAPI(title="SRE Observability Lab - API")

FastAPIInstrumentor.instrument_app(app)

# SLIs Metrics (Request Latency & Error Rate)
REQUEST_COUNT = Counter(
    'http_requests_total', 'Total HTTP Requests', 
    ['method', 'endpoint', 'http_status']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 'HTTP request latency',
    ['method', 'endpoint']
)

@app.middleware("http")
async def monitor_requests(request, call_next):
    start_time = time.time()
    
    # Simulate some real-world latency
    # In production, this would be the actual service logic
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Recording metrics
    REQUEST_COUNT.labels(
        method=request.method, 
        endpoint=request.url.path, 
        http_status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method, 
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/")
async def root():
    return {"message": "SRE Platform is Operational"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/orders")
async def get_orders():
    # Simule one real-world latency between 100ms and 1s
    # In production, this would be the actual service logic, e.g., database calls, external API requests, etc.
    delay = random.uniform(0.1, 1.0)
    time.sleep(delay)
    
    # Simulate a 20% error rate for demonstration purposes
    if random.random() < 0.2:
        REQUEST_COUNT.labels(method="GET", endpoint="/orders", http_status=500).inc()
        return Response(content="Internal Server Error", status_code=500)
    
    return {"orders": [{"id": 1, "item": "SRE Book"}, {"id": 2, "item": "Coffee"}]}