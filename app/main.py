import time
import random
import asyncio # Added for non-blocking sleep
from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Correct OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

tracer = trace.get_tracer(__name__)

# --- OpenTelemetry Setup ---
resource = Resource(attributes={
    SERVICE_NAME: "sre-observability-platform"
})

provider = TracerProvider(resource=resource)
# Fixed: Only one processor and the correct class name OTLPSpanExporter
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://jaeger:4317", insecure=True))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

app = FastAPI(title="SRE Observability Lab - API")

# Important: Instrument BEFORE defining the routes
FastAPIInstrumentor.instrument_app(app)

# --- Metrics Setup ---
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
    response = await call_next(request)
    duration = time.time() - start_time
    
    # The middleware centralizes metrics collection
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
    # SRE Practice: Use non-blocking sleep to simulate latency
    delay = random.uniform(0.1, 1.0)
    await asyncio.sleep(delay) 
    
    # Simulate a 20% error rate
    if random.random() < 0.2:
        # Removed manual inc() here, as the middleware already captures the 500
        return Response(content="Internal Server Error", status_code=500)
    
    return {"orders": [{"id": 1, "item": "SRE Book"}, {"id": 2, "item": "Coffee"}]}

@app.get("/orders")
async def get_orders():
   
    with tracer.start_as_current_span("process_orders_logic") as span:
        delay = random.uniform(0.1, 1.0)
        
        
        span.set_attribute("order.simulated_delay", delay)
        
        await asyncio.sleep(delay)
        
        if random.random() < 0.2:
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            span.add_event("Random failure triggered") #
            return Response(content="Internal Server Error", status_code=500)
            
        return {"orders": [{"id": 1, "item": "SRE Book"}]}