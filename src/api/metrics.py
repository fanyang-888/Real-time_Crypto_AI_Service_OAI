"""
Prometheus metrics collection
"""
import time
from prometheus_client import Counter, Histogram, Gauge
from fastapi import Request

# HTTP metrics
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_code'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

# Prediction metrics
prediction_requests_total = Counter(
    'prediction_requests_total',
    'Total prediction requests',
    ['model_variant', 'status']
)

prediction_errors_total = Counter(
    'prediction_errors_total',
    'Total prediction errors',
    ['model_variant', 'error_type']
)

# Kafka consumer metrics
kafka_consumer_lag = Gauge(
    'kafka_consumer_lag',
    'Kafka consumer lag in messages',
    ['topic', 'partition']
)

# Model metrics
model_load_time = Histogram(
    'model_load_time_seconds',
    'Time taken to load model',
    ['model_variant']
)

model_version = Gauge(
    'model_version_info',
    'Current model version',
    ['model_variant', 'version']
)


def setup_metrics():
    """Initialize metrics"""
    pass


async def metrics_middleware(request: Request, call_next):
    """Middleware to collect HTTP metrics"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    status_code = response.status_code
    
    # Record metrics
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=status_code
    ).inc()
    
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=status_code
    ).observe(duration)
    
    return response

