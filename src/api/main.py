"""
FastAPI main application entry point
"""
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from .routes import router
from .metrics import setup_metrics, metrics_middleware
from .model_loader import ModelLoader

# Global model loader instance
model_loader = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global model_loader
    
    # Startup
    print("Starting up...")
    model_loader = ModelLoader()
    await model_loader.load_model()
    app.state.model_loader = model_loader
    print("Model loaded successfully")
    
    yield
    
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Real-Time Crypto AI Volatility Service",
    description="Real-time cryptocurrency volatility prediction API",
    version="1.0.0",
    lifespan=lifespan
)

# Add metrics middleware
app.middleware("http")(metrics_middleware)

# Setup Prometheus metrics
setup_metrics()

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routes
app.include_router(router)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

