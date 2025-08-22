# Cognito Configuration API Routes
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

router = APIRouter(prefix="/api/v1/auth", tags=["cognito-config"])

class CognitoConfigResponse(BaseModel):
    authority: str
    client_id: str
    redirect_uri: str
    response_type: str
    scope: str
    region: str
    user_pool_id: str

@router.get("/cognito-config", response_model=CognitoConfigResponse)
async def get_cognito_config():
    """
    Get Cognito configuration for frontend
    Returns OIDC configuration for React app
    """
    user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
    client_id = os.getenv("COGNITO_CLIENT_ID")
    region = os.getenv("COGNITO_REGION", "us-east-1")
    
    if not user_pool_id or not client_id:
        raise HTTPException(
            status_code=500,
            detail="Cognito configuration is not properly set up"
        )
    
    authority = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
    
    return CognitoConfigResponse(
        authority=authority,
        client_id=client_id,
        redirect_uri="http://localhost:3000/auth/callback",
        response_type="code",
        scope="phone openid email profile",
        region=region,
        user_pool_id=user_pool_id
    )
