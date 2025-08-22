"""
Multi-tenant CodeFlowOps API with secure credential management.
Handles thousands of concurrent users with isolated credentials.
"""

import os
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# FastAPI and Pydantic
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# AWS and security
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Internal imports
from routers.registry import StackRouterRegistry
from enhanced_repository_analyzer import RepositoryAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# MODELS
# ============================================

class SessionCredentials(BaseModel):
    """Temporary session credentials for a user."""
    session_id: str
    user_id: str
    tenant_id: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_session_token: Optional[str] = None
    aws_region: str
    expires_at: datetime
    permissions: Dict[str, Any] = {}

class CredentialValidationRequest(BaseModel):
    """Request model for credential validation."""
    aws_access_key: str = Field(..., description="AWS Access Key ID")
    aws_secret_key: str = Field(..., description="AWS Secret Access Key") 
    aws_region: str = Field(default="us-east-1", description="AWS Region")
    session_name: Optional[str] = Field(None, description="Optional session name")
    session_duration: int = Field(default=3600, description="Session duration in seconds")

class UserContext(BaseModel):
    """User context for multi-tenant operations."""
    user_id: str
    tenant_id: str
    session_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class RepositoryAnalysisRequest(BaseModel):
    """Request for repository analysis with user context."""
    repo_url: str
    analysis_type: str = "full"
    user_context: UserContext

class DeploymentRequest(BaseModel):
    """Deployment request with session-based credentials."""
    session_id: str
    analysis_id: str
    deployment_config: Optional[Dict[str, Any]] = None

# ============================================
# CREDENTIAL SESSION MANAGER
# ============================================

class CredentialSessionManager:
    """Manages temporary credential sessions for concurrent users."""
    
    def __init__(self):
        self.active_sessions: Dict[str, SessionCredentials] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
        self.cleanup_interval = 300  # 5 minutes
        
    async def validate_and_create_session(
        self, 
        request: CredentialValidationRequest,
        user_context: UserContext
    ) -> SessionCredentials:
        """
        Validate credentials and create a temporary session.
        
        This approach allows thousands of users to have their own credential sessions
        without storing permanent credentials in the system.
        """
        try:
            # Create boto3 session with provided credentials
            session = boto3.Session(
                aws_access_key_id=request.aws_access_key,
                aws_secret_access_key=request.aws_secret_key,
                region_name=request.aws_region
            )
            
            # Test credentials by calling STS get_caller_identity
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            # Create temporary session credentials using STS
            # This provides time-limited credentials for the user
            session_name = request.session_name or f"codeflowops-{user_context.user_id[:8]}"
            
            # Get session token for additional security
            token_response = sts.get_session_token(
                DurationSeconds=min(request.session_duration, 3600)  # Max 1 hour
            )
            
            credentials = token_response['Credentials']
            session_id = str(uuid.uuid4())
            expires_at = credentials['Expiration']
            
            # Create session object
            session_creds = SessionCredentials(
                session_id=session_id,
                user_id=user_context.user_id,
                tenant_id=user_context.tenant_id,
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                aws_region=request.aws_region,
                expires_at=expires_at,
                permissions={
                    "account_id": identity.get("Account"),
                    "user_id": identity.get("UserId"),
                    "arn": identity.get("Arn")
                }
            )
            
            # Store session
            self.active_sessions[session_id] = session_creds
            
            # Track user sessions
            if user_context.user_id not in self.user_sessions:
                self.user_sessions[user_context.user_id] = []
            self.user_sessions[user_context.user_id].append(session_id)
            
            logger.info(f"Created session {session_id} for user {user_context.user_id} in tenant {user_context.tenant_id}")
            
            return session_creds
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code in ['InvalidUserID.NotFound', 'AuthFailure', 'SignatureDoesNotMatch']:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid AWS credentials"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"AWS API error: {error_code}"
                )
        except Exception as e:
            logger.error(f"Session creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create credential session"
            )
    
    def get_session(self, session_id: str) -> Optional[SessionCredentials]:
        """Get active session by ID."""
        session = self.active_sessions.get(session_id)
        
        # Check if session is expired
        if session and session.expires_at < datetime.utcnow():
            self.revoke_session(session_id)
            return None
            
        return session
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke a specific session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            del self.active_sessions[session_id]
            
            # Remove from user tracking
            if session.user_id in self.user_sessions:
                if session_id in self.user_sessions[session.user_id]:
                    self.user_sessions[session.user_id].remove(session_id)
                    
            logger.info(f"Revoked session {session_id}")
            return True
        return False
    
    def revoke_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a specific user."""
        if user_id not in self.user_sessions:
            return 0
            
        session_ids = self.user_sessions[user_id].copy()
        revoked_count = 0
        
        for session_id in session_ids:
            if self.revoke_session(session_id):
                revoked_count += 1
                
        return revoked_count
    
    async def cleanup_expired_sessions(self):
        """Background task to clean up expired sessions."""
        while True:
            try:
                current_time = datetime.utcnow()
                expired_sessions = [
                    session_id for session_id, session in self.active_sessions.items()
                    if session.expires_at < current_time
                ]
                
                for session_id in expired_sessions:
                    self.revoke_session(session_id)
                
                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                    
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
                
            await asyncio.sleep(self.cleanup_interval)

# ============================================
# GLOBAL MANAGERS
# ============================================

# Initialize managers
session_manager = CredentialSessionManager()
analyzer = RepositoryAnalyzer()
router_registry = StackRouterRegistry()

# ============================================
# API SETUP
# ============================================

app = FastAPI(
    title="CodeFlowOps Multi-Tenant SaaS API",
    description="Secure multi-tenant deployment platform with session-based credential management",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

# ============================================
# UTILITY FUNCTIONS
# ============================================

def extract_user_context(request: Request) -> UserContext:
    """Extract user context from request."""
    # TODO: In production, extract from JWT token
    # For now, use headers or generate temporary context
    
    user_id = request.headers.get("X-User-ID", str(uuid.uuid4()))
    tenant_id = request.headers.get("X-Tenant-ID", str(uuid.uuid4())) 
    session_id = request.headers.get("X-Session-ID", str(uuid.uuid4()))
    
    return UserContext(
        user_id=user_id,
        tenant_id=tenant_id,
        session_id=session_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )

def get_session_boto3_client(session_id: str, service_name: str):
    """Get AWS client using session credentials."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    return boto3.client(
        service_name,
        aws_access_key_id=session.aws_access_key_id,
        aws_secret_access_key=session.aws_secret_access_key,
        aws_session_token=session.aws_session_token,
        region_name=session.aws_region
    )

# ============================================
# API ENDPOINTS
# ============================================

@router.post("/api/auth/validate-credentials")
async def validate_credentials_and_create_session(
    request: CredentialValidationRequest,
    http_request: Request
):
    """
    Validate AWS credentials and create a secure session.
    
    This endpoint:
    1. Validates the provided AWS credentials
    2. Creates temporary session credentials via STS
    3. Returns a session ID for subsequent API calls
    4. Supports thousands of concurrent users with isolated sessions
    """
    user_context = extract_user_context(http_request)
    
    session_creds = await session_manager.validate_and_create_session(
        request, user_context
    )
    
    return {
        "success": True,
        "valid": True,
        "session_id": session_creds.session_id,
        "expires_at": session_creds.expires_at.isoformat(),
        "aws_region": session_creds.aws_region,
        "permissions": session_creds.permissions,
        "message": "Credentials validated and session created"
    }

@router.get("/api/auth/session/{session_id}")
async def get_session_info(session_id: str):
    """Get information about an active session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )
    
    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "tenant_id": session.tenant_id,
        "aws_region": session.aws_region,
        "expires_at": session.expires_at.isoformat(),
        "permissions": session.permissions
    }

@router.delete("/api/auth/session/{session_id}")
async def revoke_session(session_id: str):
    """Revoke a specific session."""
    revoked = session_manager.revoke_session(session_id)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return {"success": True, "message": "Session revoked"}

@router.post("/api/analyze-repo")
async def analyze_repository_with_session(request: RepositoryAnalysisRequest):
    """
    Analyze repository with user session context.
    Each analysis is tied to a specific user session.
    """
    # Verify session exists
    session = session_manager.get_session(request.user_context.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    try:
        # Generate deployment ID for this analysis
        deployment_id = str(uuid.uuid4())
        
        logger.info(f"Starting repository analysis for session {session.session_id}")
        
        # Perform analysis
        analysis = await analyzer.analyze_repository_comprehensive(
            request.repo_url, 
            deployment_id
        )
        
        # Get available stack routers
        available_routers = router_registry.get_available_routers()
        detected_stack = None
        
        # Determine deployment endpoint based on detected stack
        if analysis.get("stack_blueprint", {}).get("final_recommendation", {}).get("stack_id"):
            stack_id = analysis["stack_blueprint"]["final_recommendation"]["stack_id"]
            # Extract stack type (e.g., "react" from "aws.s3.cloudfront.create-react-app.v1")
            for router_name in available_routers:
                if router_name.lower() in stack_id.lower():
                    detected_stack = router_name
                    break
        
        return {
            "success": True,
            "analysis": analysis,
            "analysis_id": deployment_id,
            "session_id": session.session_id,
            "user_id": session.user_id,
            "tenant_id": session.tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "modular_system_available": True,
            "available_stacks": available_routers,
            "detected_stack": detected_stack,
            "deployment_endpoint": f"/api/deploy/{detected_stack}" if detected_stack else "/api/deploy"
        }
        
    except Exception as e:
        logger.error(f"Repository analysis failed for session {session.session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@router.post("/api/deploy")
async def deploy_with_session(request: DeploymentRequest):
    """
    Deploy using session-based credentials.
    Uses the session's AWS credentials for deployment.
    """
    # Get session
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    try:
        # TODO: Implement deployment logic using session credentials
        # This would use session.aws_access_key_id, session.aws_secret_access_key, etc.
        
        deployment_id = str(uuid.uuid4())
        
        return {
            "success": True,
            "deployment_id": deployment_id,
            "session_id": session.session_id,
            "status": "deployment_started",
            "message": "Deployment initiated with session credentials"
        }
        
    except Exception as e:
        logger.error(f"Deployment failed for session {session.session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {str(e)}"
        )

@router.get("/api/system/health")
async def health_check():
    """System health check."""
    active_sessions_count = len(session_manager.active_sessions)
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_sessions": active_sessions_count,
        "service": "CodeFlowOps Multi-Tenant API"
    }

@router.get("/api/system/stats")
async def system_stats():
    """Get system statistics."""
    return {
        "active_sessions": len(session_manager.active_sessions),
        "total_users": len(session_manager.user_sessions),
        "available_stacks": router_registry.get_available_routers(),
        "system_status": "operational"
    }

# ============================================
# APPLICATION SETUP
# ============================================

# Include router
app.include_router(router)

# Start background tasks
@app.on_event("startup")
async def startup_event():
    """Start background tasks."""
    asyncio.create_task(session_manager.cleanup_expired_sessions())
    logger.info("CodeFlowOps Multi-Tenant API started")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
