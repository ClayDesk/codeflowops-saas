# Routes package for CodeFlowOps
from fastapi import APIRouter
import types

# Create a simple class to hold router attributes
class RouteModule:
    def __init__(self, name: str):
        self.name = name
        self.router = APIRouter()

# Import routers from each route module, or create empty ones
try:
    from . import analysis_routes
    if not hasattr(analysis_routes, 'router'):
        analysis_routes.router = APIRouter()
except ImportError:
    analysis_routes = RouteModule('analysis_routes')

try:
    from . import deployment_routes
    if not hasattr(deployment_routes, 'router'):
        deployment_routes.router = APIRouter()
except ImportError:
    deployment_routes = RouteModule('deployment_routes')

try:
    from . import session_routes
    if not hasattr(session_routes, 'router'):
        session_routes.router = APIRouter()
except ImportError:
    session_routes = RouteModule('session_routes')

try:
    from . import health_routes
    if not hasattr(health_routes, 'router'):
        health_routes.router = APIRouter()
except ImportError:
    health_routes = RouteModule('health_routes')

try:
    from . import job_routes
    if not hasattr(job_routes, 'router'):
        job_routes.router = APIRouter()
except ImportError:
    job_routes = RouteModule('job_routes')

try:
    from . import dashboard_routes
    if not hasattr(dashboard_routes, 'router'):
        dashboard_routes.router = APIRouter()
except ImportError:
    dashboard_routes = RouteModule('dashboard_routes')

try:
    from . import session_management_routes
    if not hasattr(session_management_routes, 'router'):
        session_management_routes.router = APIRouter()
except ImportError:
    session_management_routes = RouteModule('session_management_routes')

try:
    from . import admin_routes
    if not hasattr(admin_routes, 'router'):
        admin_routes.router = APIRouter()
except ImportError:
    admin_routes = RouteModule('admin_routes')

try:
    from . import admin_billing_routes
    if not hasattr(admin_billing_routes, 'router'):
        admin_billing_routes.router = APIRouter()
except ImportError:
    admin_billing_routes = RouteModule('admin_billing_routes')

try:
    from . import billing_routes
    if not hasattr(billing_routes, 'router'):
        billing_routes.router = APIRouter()
except ImportError:
    billing_routes = RouteModule('billing_routes')

try:
    from . import websocket_routes
    if not hasattr(websocket_routes, 'router'):
        websocket_routes.router = APIRouter()
except ImportError:
    websocket_routes = RouteModule('websocket_routes')

# Create stack_routes since it doesn't exist
stack_routes = RouteModule('stack_routes')

__all__ = [
    "analysis_routes",
    "deployment_routes", 
    "session_routes",
    "stack_routes",
    "health_routes",
    "job_routes",
    "dashboard_routes",
    "session_management_routes",
    "admin_routes",
    "admin_billing_routes",
    "billing_routes",
    "websocket_routes"
]
