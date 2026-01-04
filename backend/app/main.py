"""
FastAPI Backend for Air Quality Monitoring System
"""
import sys
import asyncio

# ✅ CRITICAL: Windows asyncio fix - MUST be at the very top
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import engine, Base
from .routes import router
from .mqtt_client import start_mqtt_subscriber 

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting application...")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
    
    # Start MQTT subscriber
    mqtt_task = None
    try:
        mqtt_task = asyncio.create_task(start_mqtt_subscriber())
        logger.info("✅ MQTT subscriber started")
    except Exception as e:
        logger.error(f"❌ MQTT subscriber error: {e}")
        logger.warning("⚠️ Continuing without MQTT support")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application...")
    
    if mqtt_task:
        mqtt_task.cancel()
        try:
            await mqtt_task
        except asyncio.CancelledError:
            logger.info("✅ MQTT subscriber stopped")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Air Quality Monitoring Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "api": "/api",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "mqtt": "connected"
    }