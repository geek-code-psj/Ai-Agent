"""Prometheus metrics middleware."""

import time
from typing import Callable
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge
from starlette.middleware.base import BaseHTTPMiddleware

# Prometheus metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint']
)

agent_executions_total = Counter(
    'agent_executions_total',
    'Total agent executions',
    ['agent_type', 'status']
)

agent_execution_duration_seconds = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration in seconds',
    ['agent_type']
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Skip metrics for metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Extract method and path
        method = request.method
        path = request.url.path
        
        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=path).inc()
        
        # Record start time
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code
            
            # Record metrics
            duration = time.time() - start_time
            http_requests_total.labels(
                method=method,
                endpoint=path,
                status=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Record error
            http_requests_total.labels(
                method=method,
                endpoint=path,
                status=500
            ).inc()
            raise
            
        finally:
            # Decrement in-progress
            http_requests_in_progress.labels(method=method, endpoint=path).dec()


def record_agent_execution(agent_type: str, duration: float, status: str = "success"):
    """
    Record agent execution metrics.
    
    Args:
        agent_type: Type of agent
        duration: Execution duration in seconds
        status: Execution status ('success' or 'error')
    """
    agent_executions_total.labels(agent_type=agent_type, status=status).inc()
    agent_execution_duration_seconds.labels(agent_type=agent_type).observe(duration)
