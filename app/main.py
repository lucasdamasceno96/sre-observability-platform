import time
import random
from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="SRE Observability Lab - API")

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