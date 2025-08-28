"""
CodeFlowOps FastAPI Application
Enhanced repository analysis and deployment automation platform
"""

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging
import os
from contextlib import asynccontextmanager

# Import enhanced analysis and deployment APIs
try:
    from .api.analysis import router as analysis_router
    from .api.deployment import router as deployment_router
except ImportError:
    from api.analysis import router as analysis_router
    from api.deployment import router as deployment_router

# Claude integration removed - using traditional Terraform templates

# Import existing route modules (if they exist)
LEGACY_ROUTES_AVAILABLE = False
analysis_routes = None
deployment_routes = None
session_routes = None
stack_routes = None
health_routes = None
job_routes = None
dashboard_routes = None
session_management_routes = None
admin_routes = None

try:
    import importlib
    # Try to import routes module
    try:
        routes_module = importlib.import_module('.routes', package=__package__)
    except ImportError:
        routes_module = importlib.import_module('routes')
    
    # Get individual route modules
    analysis_routes = getattr(routes_module, 'analysis_routes', None)
    deployment_routes = getattr(routes_module, 'deployment_routes', None)
    session_routes = getattr(routes_module, 'session_routes', None)
    stack_routes = getattr(routes_module, 'stack_routes', None)
    health_routes = getattr(routes_module, 'health_routes', None)
    job_routes = getattr(routes_module, 'job_routes', None)
    dashboard_routes = getattr(routes_module, 'dashboard_routes', None)
    session_management_routes = getattr(routes_module, 'session_management_routes', None)
    admin_routes = getattr(routes_module, 'admin_routes', None)
    
    LEGACY_ROUTES_AVAILABLE = True
except ImportError:
    pass  # Routes not available

try:
    from .api.auth_routes import router as auth_router
    AUTH_AVAILABLE = True
    print("✅ Simple Cognito auth routes loaded successfully")
except ImportError:
    try:
        from api.auth_routes import router as auth_router
        AUTH_AVAILABLE = True
        print("✅ Simple Cognito auth routes loaded successfully (fallback)")
    except ImportError:
        AUTH_AVAILABLE = False
        print("⚠️ Auth routes not available")

# Import configuration (with fallback)
try:
    from .config.env import get_settings
    settings = get_settings()
except ImportError:
    try:
        from .config.env import get_settings
        settings = get_settings()
    except ImportError:
        # Fallback configuration
        class Settings:
            LOG_LEVEL = "INFO"
            ENVIRONMENT = "development"
            AWS_REGION = "us-east-1"
        settings = Settings()

# Setup logging
logging.basicConfig(
    level=getattr(logging, getattr(settings, 'LOG_LEVEL', 'INFO'), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events"""
    # Startup
    logger.info("Starting CodeFlowOps Enhanced Analysis Engine")
    logger.info("Phase 1: Enhanced Repository Analysis Engine - ACTIVE")
    logger.info(f"Environment: {getattr(settings, 'ENVIRONMENT', 'development')}")
    logger.info(f"AWS Region: {getattr(settings, 'AWS_REGION', 'us-east-1')}")
    
    # Initialize enhanced analysis engine
    logger.info("Initializing enhanced repository analysis engine...")
    
    # Try to run legacy startup tasks if available
    try:
        from .utils.startup import startup_tasks
        await startup_tasks()
        logger.info("Legacy startup tasks completed")
    except ImportError:
        try:
            from .utils.startup import startup_tasks
            await startup_tasks()
            logger.info("Legacy startup tasks completed")
        except ImportError:
            logger.info("No legacy startup tasks found, proceeding with enhanced engine only")
    
    # Try to initialize WebSocket manager if available
    try:
        from .utils.websocket_manager import get_websocket_manager
        websocket_manager = get_websocket_manager()
        logger.info("WebSocket manager initialized")
    except ImportError:
        try:
            from .utils.websocket_manager import get_websocket_manager
            websocket_manager = get_websocket_manager()
            logger.info("WebSocket manager initialized")
        except ImportError:
            logger.info("WebSocket manager not available")
    
    # Try to initialize job processor if available
    try:
        from .background.job_processor import start_job_processor
        import asyncio
        asyncio.create_task(start_job_processor())
        logger.info("Job processor started")
    except ImportError:
        try:
            from background.job_processor import start_job_processor
            import asyncio
            asyncio.create_task(start_job_processor())
            logger.info("Job processor started")
        except ImportError:
            logger.info("Background job processor not available")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CodeFlowOps Enhanced Analysis Engine")
    
    # Try graceful shutdown of legacy components
    try:
        from .background.job_processor import stop_job_processor
        await stop_job_processor()
        logger.info("Job processor stopped")
    except ImportError:
        pass
    
    try:
        from .database.connection import close_database
        await close_database()
        logger.info("Database connections closed")
    except ImportError:
        pass


# Create FastAPI application with enhanced configuration
app = FastAPI(
    title="CodeFlowOps Enhanced Analysis Engine",
    description="Enhanced repository analysis and deployment automation platform",
    version="1.0.0",
    docs_url="/docs" if getattr(settings, 'NODE_ENV', 'development') != "production" else None,
    redoc_url="/redoc" if getattr(settings, 'NODE_ENV', 'development') != "production" else None,
    lifespan=lifespan
)

# Configure CORS dynamically
allowed_origins = getattr(settings, 'ALLOWED_ORIGINS', '').split(",") if getattr(settings, 'ALLOWED_ORIGINS', '') else [
    "https://www.codeflowops.com",  # Production frontend
    "https://codeflowops.com",      # Production frontend (without www)
    "http://localhost:3000",        # React dev server
    "http://localhost:5173",        # Vite dev server
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add trusted host middleware for production
if getattr(settings, 'ENVIRONMENT', 'development') == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["api.codeflowops.com", "*.codeflowops.com", "codeflowops.com"]
    )

# TODO: Add rate limiting middleware
# app.middleware("http")(rate_limit_middleware)


# Request timing middleware for performance monitoring
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests (with fallback threshold)
    slow_threshold = getattr(settings, 'SLOW_REQUEST_THRESHOLD', 2.0)
    if process_time > slow_threshold:
        logger.warning(f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s")
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again.",
            "request_id": getattr(request.state, "request_id", None)
        }
    )

# Include enhanced analysis router (Priority #1)
app.include_router(analysis_router)

# Include enhanced deployment router (Priority #2)
app.include_router(deployment_router)

# Claude integration removed - using traditional Terraform templates

# Include Smart Deploy router with traditional templates (Priority #4)
try:
    from .api.smart_deploy_routes import router as smart_deploy_router
    app.include_router(smart_deploy_router)
    logger.info("✅ Smart Deploy router with traditional templates loaded successfully")
except ImportError as e:
    logger.error(f"❌ Failed to load Smart Deploy router (ImportError): {e}")
except Exception as e:
    logger.error(f"❌ Failed to load Smart Deploy router: {e}")

# Include WebSocket routes for real-time monitoring
try:
    from .routes.websocket_routes import router as websocket_router
    app.include_router(
        websocket_router,
        prefix="/api",
        tags=["Real-time Monitoring"]
    )
    logger.info("✅ WebSocket real-time monitoring enabled")
except ImportError:
    try:
        from routes.websocket_routes import router as websocket_router
        app.include_router(
            websocket_router,
            prefix="/api",
            tags=["Real-time Monitoring"]
        )
        logger.info("✅ WebSocket real-time monitoring enabled")
    except ImportError:
        logger.warning("WebSocket routes not available")

# Include legacy routers if available
if AUTH_AVAILABLE:
    app.include_router(
        auth_router,
        prefix="/api/auth",
        tags=["Authentication"]
    )

# Include GitHub auth routes
try:
    from .api.github_auth_routes import router as github_auth_router
    app.include_router(
        github_auth_router,
        prefix="/api/v1",
        tags=["GitHub Authentication"]
    )
    logger.info("✅ GitHub authentication routes loaded successfully")
except ImportError:
    try:
        from api.github_auth_routes import router as github_auth_router
        app.include_router(
            github_auth_router,
            prefix="/api/v1",
            tags=["GitHub Authentication"]
        )
        logger.info("✅ GitHub authentication routes loaded successfully (fallback)")
    except ImportError:
        logger.warning("⚠️ GitHub auth routes not available")

if LEGACY_ROUTES_AVAILABLE:
    if health_routes and hasattr(health_routes, 'router'):
        app.include_router(
            health_routes.router,
            prefix="/api/health",
            tags=["Health"]
        )

    if analysis_routes and hasattr(analysis_routes, 'router'):
        app.include_router(
            analysis_routes.router,
            prefix="/api",
            tags=["Analysis"]
        )

    if deployment_routes and hasattr(deployment_routes, 'router'):
        app.include_router(
            deployment_routes.router,
            prefix="/api",
            tags=["Deployment"]
        )

    if session_routes and hasattr(session_routes, 'router'):
        app.include_router(
            session_routes.router,
            prefix="/api",
            tags=["Session Management"]
        )

    if stack_routes and hasattr(stack_routes, 'router'):
        app.include_router(
            stack_routes.router,
            prefix="/api",
            tags=["Infrastructure Stacks"]
        )

    if job_routes and hasattr(job_routes, 'router'):
        app.include_router(
            job_routes.router,
            prefix="/api",
            tags=["Job Management"]
        )

    if dashboard_routes and hasattr(dashboard_routes, 'router'):
        app.include_router(
            dashboard_routes.router,
            prefix="/api",
            tags=["Dashboard"]
        )

    if session_management_routes and hasattr(session_management_routes, 'router'):
        app.include_router(
            session_management_routes.router,
            prefix="/api",
            tags=["Session Management"]
        )

    if admin_routes and hasattr(admin_routes, 'router'):
        app.include_router(
            admin_routes.router,
            prefix="/api",
            tags=["Admin Panel"]
        )

    # Billing routes removed (Stripe functionality removed)
    logger.info("Billing functionality has been removed from the application")


# Enhanced root endpoint
@app.get("/")
async def root():
    return {
        "message": "CodeFlowOps Enhanced Analysis Engine",
        "version": "1.0.0",
        "status": "operational",
        "description": "Enhanced repository analysis and deployment automation platform",
        "current_phase": "Phase 1: Enhanced Repository Analysis Engine",
        "features": [
            "Deep repository structure analysis",
            "Advanced project type detection",
            "Comprehensive dependency analysis",
            "Security vulnerability scanning",
            "Build configuration recommendations",
            "Deployment readiness assessment"
        ],
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "analysis": "/api/analysis",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    return {
        "status": "healthy",
        "service": "codeflowops-enhanced-analysis-engine",
        "version": "1.0.0",
        "phase": "Phase 1: Enhanced Repository Analysis Engine",
        "components": {
            "api": "operational",
            "analysis_engine": "operational",
            "repository_analyzer": "operational",
            "project_detector": "operational",
            "dependency_analyzer": "operational",
            "legacy_routes": "available" if LEGACY_ROUTES_AVAILABLE else "unavailable",
            "auth": "available" if AUTH_AVAILABLE else "unavailable"
        }
    }


# Enhanced WebSocket endpoint for real-time updates (if dependencies available)
try:
    from fastapi import WebSocket, WebSocketDisconnect
    from .dependencies.session import get_session_manager

    @app.websocket("/ws/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        """Real-time deployment progress updates"""
        await websocket.accept()
        
        session_manager = await get_session_manager()
        if hasattr(session_manager, 'add_websocket_connection'):
            await session_manager.add_websocket_connection(session_id, websocket)
        
        try:
            while True:
                # Keep connection alive and handle client messages
                data = await websocket.receive_text()
                
                # Echo back for connection health check
                if data == "ping":
                    await websocket.send_text("pong")
                    
        except WebSocketDisconnect:
            if hasattr(session_manager, 'remove_websocket_connection'):
                await session_manager.remove_websocket_connection(session_id, websocket)
            logger.info(f"WebSocket disconnected for session: {session_id}")
        except Exception as e:
            logger.error(f"WebSocket error for session {session_id}: {str(e)}")
            if hasattr(session_manager, 'remove_websocket_connection'):
                await session_manager.remove_websocket_connection(session_id, websocket)
            
except ImportError:
    logger.info("WebSocket dependencies not available, skipping WebSocket endpoint")


# Enhanced version endpoint
@app.get("/api/version")
async def get_version():
    """Get API version information"""
    return {
        "version": "1.0.0",
        "api_version": "v1",
        "phase": "Phase 1: Enhanced Repository Analysis Engine",
        "features": {
            "repository_analysis": "enabled",
            "project_type_detection": "enabled",
            "dependency_analysis": "enabled",
            "security_scanning": "enabled",
            "stack_recommendation": "coming_soon",
            "enhancement_engine": "coming_soon",
            "build_automation": "coming_soon",
            "terraform_deployment": "coming_soon"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Dynamic server configuration with fallbacks
    host = getattr(settings, 'HOST', '0.0.0.0')
    port = getattr(settings, 'PORT', 8000)
    node_env = getattr(settings, 'NODE_ENV', 'development')
    log_level = getattr(settings, 'LOG_LEVEL', 'info')
    workers = getattr(settings, 'WORKERS', 1)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=node_env == "development",
        log_level=log_level.lower(),
        workers=workers if node_env == "production" else 1
    )
