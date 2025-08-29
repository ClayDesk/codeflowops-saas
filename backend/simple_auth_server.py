#!/usr/bin/env python3
"""
Simple FastAPI server with working auth routes
Bypasses all import issues by keeping everything in one file
"""
import os
import sys
import asyncio
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Optional

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import logging

# Simple data models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    verification_code: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    verification_code: str
    new_password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int = 3600
    user: dict

# Simple in-memory storage
pending_registrations = {}
verification_codes = {}
password_reset_codes = {}
verified_users = {}

# Create FastAPI app
app = FastAPI(title="CodeFlowOps Auth API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple email service
async def send_email_code(email: str, code: str) -> bool:
    """Send verification code via email"""
    try:
        # Load environment
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
        
        # Import email service
        sys.path.insert(0, os.path.dirname(__file__))
        from services.email_service import EmailService
        
        email_service = EmailService()
        result = await email_service.send_verification_code(email, code)
        logger.info(f"Email sent to {email}: {result}")
        return result
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False

# Auth routes
@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    """Register new user with email verification"""
    logger.info(f"Registration attempt: {request.email}")
    
    try:
        # Generate verification code
        verification_code = ''.join(random.choices(string.digits, k=6))
        logger.info(f"Generated code {verification_code} for {request.email}")
        
        # Send email
        email_sent = await send_email_code(request.email, verification_code)
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
        
        # Store pending registration
        pending_registrations[request.email] = {
            "email": request.email,
            "password": request.password,
            "full_name": request.full_name,
            "created_at": datetime.utcnow().isoformat()
        }
        
        verification_codes[request.email] = {
            "code": verification_code,
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }
        
        logger.info(f"Registration pending for {request.email}")
        return {
            "message": "Verification code sent to your email. Please verify to complete registration.",
            "email": request.email,
            "requires_verification": True
        }
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/api/v1/auth/verify-email", response_model=LoginResponse)
async def verify_email(request: VerifyEmailRequest):
    """Verify email and complete registration"""
    logger.info(f"Email verification attempt: {request.email}")
    
    # Check if verification code exists and is valid
    if request.email not in verification_codes:
        logger.warning(f"No verification code found for {request.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    stored_code = verification_codes[request.email]
    
    # Check expiration
    if datetime.utcnow() > stored_code["expires_at"]:
        logger.warning(f"Verification code expired for {request.email}")
        del verification_codes[request.email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired"
        )
    
    # Check code match
    if stored_code["code"] != request.verification_code:
        logger.warning(f"Invalid verification code for {request.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Get pending registration
    if request.email not in pending_registrations:
        logger.error(f"No pending registration found for {request.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending registration found"
        )
    
    # Create verified user
    pending_reg = pending_registrations[request.email]
    user_id = f"user-{random.randint(100000, 999999)}"
    
    verified_users[request.email] = {
        "id": user_id,
        "email": request.email,
        "username": request.email,
        "full_name": pending_reg.get("full_name"),
        "password": pending_reg["password"],  # In production, hash this
        "provider": "email",
        "verified": True,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Clean up
    del verification_codes[request.email]
    del pending_registrations[request.email]
    
    # Generate simple token
    access_token = f"token-{user_id}-{random.randint(100000, 999999)}"
    
    logger.info(f"Email verification successful for {request.email}")
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=f"refresh-{user_id}-{random.randint(100000, 999999)}",
        user={
            "id": user_id,
            "email": request.email,
            "username": request.email,
            "full_name": pending_reg.get("full_name"),
            "provider": "email"
        }
    )

@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login with email and password"""
    logger.info(f"Login attempt: {request.email}")
    
    # Check if user exists and is verified
    if request.email not in verified_users:
        logger.warning(f"User not found: {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    user = verified_users[request.email]
    
    # Check password (in production, use proper hashing)
    if user["password"] != request.password:
        logger.warning(f"Invalid password for {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate tokens
    access_token = f"token-{user['id']}-{random.randint(100000, 999999)}"
    refresh_token = f"refresh-{user['id']}-{random.randint(100000, 999999)}"
    
    logger.info(f"Login successful for {request.email}")
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
            "full_name": user["full_name"],
            "provider": user["provider"]
        }
    )

@app.post("/api/v1/auth/resend-verification")
async def resend_verification(request: dict):
    """Resend verification code"""
    email = request.get("email")
    logger.info(f"Resend verification for: {email}")
    
    if email not in pending_registrations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending registration found"
        )
    
    # Generate new verification code
    verification_code = ''.join(random.choices(string.digits, k=6))
    
    # Send email
    email_sent = await send_email_code(email, verification_code)
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
    
    # Update stored code
    verification_codes[email] = {
        "code": verification_code,
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }
    
    return {"message": "Verification code resent to your email", "email": email}

@app.post("/api/v1/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Initiate password reset"""
    logger.info(f"Password reset request for: {request.email}")
    
    # Check if user exists (but don't reveal if they don't for security)
    if request.email not in verified_users:
        # Still return success for security (don't reveal if email exists)
        return {"message": "If an account with that email exists, password reset instructions have been sent."}
    
    # Generate password reset code
    reset_code = ''.join(random.choices(string.digits, k=6))
    logger.info(f"Generated reset code {reset_code} for {request.email}")
    
    # Send email
    email_sent = await send_email_code(request.email, reset_code)
    if not email_sent:
        # For security, still return success even if email failed
        logger.error(f"Failed to send reset email to {request.email}")
        return {"message": "If an account with that email exists, password reset instructions have been sent."}
    
    # Store reset code
    password_reset_codes[request.email] = {
        "code": reset_code,
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    
    return {"message": "If an account with that email exists, password reset instructions have been sent."}

@app.post("/api/v1/auth/confirm-reset-password")
async def confirm_reset_password(request: ResetPasswordRequest):
    """Confirm password reset with verification code"""
    logger.info(f"Password reset confirmation for: {request.email}")
    
    # Check if user exists
    if request.email not in verified_users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset request"
        )
    
    # Check if reset code exists and is valid
    if request.email not in password_reset_codes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No password reset request found or code has expired"
        )
    
    reset_info = password_reset_codes[request.email]
    
    # Check if code has expired
    if datetime.utcnow() > reset_info["expires_at"]:
        del password_reset_codes[request.email]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset code has expired. Please request a new one."
        )
    
    # Check if code matches
    if reset_info["code"] != request.verification_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Validate new password (basic validation)
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Update user password
    verified_users[request.email]["password"] = request.new_password
    
    # Clean up reset code
    del password_reset_codes[request.email]
    
    logger.info(f"Password successfully reset for {request.email}")
    
    return {"message": "Password has been successfully reset. You can now log in with your new password."}

@app.get("/")
async def root():
    return {"message": "CodeFlowOps Auth API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
