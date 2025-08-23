"""
AWS Credentials Management API
Handles secure storage and validation of AWS credentials
"""

from fastapi import APIRouter, HTTPException  # type: ignore
from pydantic import BaseModel, Field  # type: ignore
from typing import Optional, List, Dict
import boto3  # type: ignore
import uuid
from datetime import datetime
import logging
from cryptography.fernet import Fernet  # type: ignore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/credentials", tags=["credentials"])

# Simple in-memory storage for demo - in production use a proper database
credentials_store = {}
encryption_key = Fernet.generate_key()
fernet = Fernet(encryption_key)

class CredentialData(BaseModel):
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    role_arn: Optional[str] = None
    external_id: Optional[str] = None
    region: str = "us-east-1"

class CredentialRequest(BaseModel):
    credential_name: str
    credential_type: str = Field(..., pattern="^(access_key|role_arn)$")
    credential_data: CredentialData
    aws_region: str = "us-east-1"
    permissions_policy: Optional[Dict] = None
    allowed_ips: List[str] = []
    mfa_required: bool = True
    max_session_duration: str = "1h"
    rotation_schedule: Optional[str] = None
    expires_at: Optional[str] = None

class ValidationRequest(BaseModel):
    credential_data: CredentialData

class ValidationResult(BaseModel):
    valid: bool
    identity: Optional[Dict] = None
    permissions: List[str] = []
    warnings: List[str] = []
    error: Optional[str] = None

class CredentialResponse(BaseModel):
    credential_id: str
    credential_name: str
    credential_type: str
    aws_region: str
    created_at: str
    status: str
    last_validated: Optional[str] = None

def encrypt_data(data: str) -> str:
    """Encrypt sensitive data"""
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    return fernet.decrypt(encrypted_data.encode()).decode()

def validate_access_keys(access_key_id: str, secret_access_key: str, region: str = "us-east-1") -> ValidationResult:
    """Validate AWS access keys"""
    try:
        # Create a session with the provided credentials
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region
        )
        
        # Test the credentials by calling STS GetCallerIdentity
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        
        # Test IAM permissions
        iam = session.client('iam')
        permissions = []
        warnings = []
        
        try:
            # Try to list attached user policies
            user_name = identity['Arn'].split('/')[-1] if 'user/' in identity['Arn'] else None
            if user_name:
                try:
                    policies = iam.list_attached_user_policies(UserName=user_name)
                    for policy in policies['AttachedPolicies']:
                        permissions.append(policy['PolicyName'])
                except Exception:
                    pass
                    
                try:
                    inline_policies = iam.list_user_policies(UserName=user_name)
                    permissions.extend(inline_policies['PolicyNames'])
                except Exception:
                    pass
        except Exception:
            warnings.append("Could not retrieve detailed permission information")
        
        # Check for common security issues
        if 'root' in identity['Arn']:
            warnings.append("Using root account credentials is not recommended")
        
        # Basic permission checks
        try:
            # Test S3 access
            s3 = session.client('s3')
            s3.list_buckets()
            permissions.append("s3:ListBuckets")
        except Exception:
            pass
            
        try:
            # Test EC2 access
            ec2 = session.client('ec2')
            ec2.describe_regions()
            permissions.append("ec2:DescribeRegions")
        except Exception:
            pass
            
        try:
            # Test CloudFormation access
            cf = session.client('cloudformation')
            cf.list_stacks()
            permissions.append("cloudformation:ListStacks")
        except Exception:
            pass
        
        return ValidationResult(
            valid=True,
            identity=identity,
            permissions=list(set(permissions)),
            warnings=warnings
        )
        
    except Exception as e:
        logger.error(f"Access key validation failed: {e}")
        return ValidationResult(
            valid=False,
            error=str(e),
            permissions=[],
            warnings=[]
        )

def validate_iam_role(role_arn: str, external_id: Optional[str] = None, region: str = "us-east-1") -> ValidationResult:
    """Validate IAM role assumption"""
    try:
        # For demo purposes, we'll simulate role validation
        # In production, you'd need to have credentials to assume the role
        
        # Basic ARN validation
        if not role_arn.startswith('arn:aws:iam::'):
            return ValidationResult(
                valid=False,
                error="Invalid role ARN format",
                permissions=[],
                warnings=[]
            )
        
        # Extract account ID and role name
        arn_parts = role_arn.split(':')
        if len(arn_parts) < 6:
            return ValidationResult(
                valid=False,
                error="Invalid role ARN format",
                permissions=[],
                warnings=[]
            )
        
        account_id = arn_parts[4]
        role_name = arn_parts[5].split('/')[-1]
        
        # Simulate successful validation for demo
        return ValidationResult(
            valid=True,
            identity={
                "Arn": role_arn,
                "Account": account_id,
                "RoleName": role_name
            },
            permissions=[
                "sts:AssumeRole",
                "s3:*",
                "ec2:*",
                "cloudformation:*"
            ],
            warnings=[
                "Role validation requires proper trust relationship configuration"
            ] if not external_id else []
        )
        
    except Exception as e:
        logger.error(f"IAM role validation failed: {e}")
        return ValidationResult(
            valid=False,
            error=str(e),
            permissions=[],
            warnings=[]
        )

@router.post("/validate", response_model=ValidationResult)
async def validate_credentials(request: ValidationRequest):
    """Validate AWS credentials without storing them"""
    try:
        credential_data = request.credential_data
        
        if credential_data.access_key_id and credential_data.secret_access_key:
            # Validate access keys
            return validate_access_keys(
                credential_data.access_key_id,
                credential_data.secret_access_key,
                credential_data.region
            )
        elif credential_data.role_arn:
            # Validate IAM role
            return validate_iam_role(
                credential_data.role_arn,
                credential_data.external_id,
                credential_data.region
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either access keys or role ARN must be provided"
            )
            
    except Exception as e:
        logger.error(f"Credential validation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )

@router.post("/", response_model=CredentialResponse)
async def create_credential(request: CredentialRequest):
    """Create and store AWS credentials securely"""
    try:
        credential_id = str(uuid.uuid4())
        
        # Encrypt sensitive data
        encrypted_data = {}
        if request.credential_data.access_key_id:
            encrypted_data['access_key_id'] = encrypt_data(request.credential_data.access_key_id)
        if request.credential_data.secret_access_key:
            encrypted_data['secret_access_key'] = encrypt_data(request.credential_data.secret_access_key)
        if request.credential_data.role_arn:
            encrypted_data['role_arn'] = encrypt_data(request.credential_data.role_arn)
        if request.credential_data.external_id:
            encrypted_data['external_id'] = encrypt_data(request.credential_data.external_id)
        
        # Store credential
        credential_record = {
            "credential_id": credential_id,
            "credential_name": request.credential_name,
            "credential_type": request.credential_type,
            "aws_region": request.aws_region,
            "encrypted_data": encrypted_data,
            "permissions_policy": request.permissions_policy,
            "allowed_ips": request.allowed_ips,
            "mfa_required": request.mfa_required,
            "max_session_duration": request.max_session_duration,
            "rotation_schedule": request.rotation_schedule,
            "expires_at": request.expires_at,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
            "last_validated": datetime.utcnow().isoformat()
        }
        
        credentials_store[credential_id] = credential_record
        
        logger.info(f"Created credential {credential_id} for {request.credential_name}")
        
        return CredentialResponse(
            credential_id=credential_id,
            credential_name=request.credential_name,
            credential_type=request.credential_type,
            aws_region=request.aws_region,
            created_at=credential_record["created_at"],
            status="active",
            last_validated=credential_record["last_validated"]
        )
        
    except Exception as e:
        logger.error(f"Failed to create credential: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create credential: {str(e)}"
        )

@router.get("/", response_model=List[CredentialResponse])
async def list_credentials():
    """List all stored credentials (without sensitive data)"""
    try:
        credentials = []
        for cred_id, cred_data in credentials_store.items():
            credentials.append(CredentialResponse(
                credential_id=cred_id,
                credential_name=cred_data["credential_name"],
                credential_type=cred_data["credential_type"],
                aws_region=cred_data["aws_region"],
                created_at=cred_data["created_at"],
                status=cred_data["status"],
                last_validated=cred_data.get("last_validated")
            ))
        
        return credentials
        
    except Exception as e:
        logger.error(f"Failed to list credentials: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list credentials: {str(e)}"
        )

@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(credential_id: str):
    """Get specific credential details (without sensitive data)"""
    try:
        if credential_id not in credentials_store:
            raise HTTPException(
                status_code=404,
                detail="Credential not found"
            )
        
        cred_data = credentials_store[credential_id]
        
        return CredentialResponse(
            credential_id=credential_id,
            credential_name=cred_data["credential_name"],
            credential_type=cred_data["credential_type"],
            aws_region=cred_data["aws_region"],
            created_at=cred_data["created_at"],
            status=cred_data["status"],
            last_validated=cred_data.get("last_validated")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get credential {credential_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get credential: {str(e)}"
        )

@router.delete("/{credential_id}")
async def delete_credential(credential_id: str):
    """Delete a credential"""
    try:
        if credential_id not in credentials_store:
            raise HTTPException(
                status_code=404,
                detail="Credential not found"
            )
        
        del credentials_store[credential_id]
        logger.info(f"Deleted credential {credential_id}")
        
        return {"message": "Credential deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete credential {credential_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete credential: {str(e)}"
        )

@router.post("/{credential_id}/validate", response_model=ValidationResult)
async def revalidate_credential(credential_id: str):
    """Re-validate an existing credential"""
    try:
        if credential_id not in credentials_store:
            raise HTTPException(
                status_code=404,
                detail="Credential not found"
            )
        
        cred_data = credentials_store[credential_id]
        encrypted_data = cred_data["encrypted_data"]
        
        # Decrypt and validate
        if cred_data["credential_type"] == "access_key":
            access_key_id = decrypt_data(encrypted_data["access_key_id"])
            secret_access_key = decrypt_data(encrypted_data["secret_access_key"])
            
            result = validate_access_keys(
                access_key_id,
                secret_access_key,
                cred_data["aws_region"]
            )
        else:  # role_arn
            role_arn = decrypt_data(encrypted_data["role_arn"])
            external_id = decrypt_data(encrypted_data.get("external_id", "")) if encrypted_data.get("external_id") else None
            
            result = validate_iam_role(
                role_arn,
                external_id,
                cred_data["aws_region"]
            )
        
        # Update last validated timestamp
        if result.valid:
            credentials_store[credential_id]["last_validated"] = datetime.utcnow().isoformat()
            credentials_store[credential_id]["status"] = "active"
        else:
            credentials_store[credential_id]["status"] = "invalid"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revalidate credential {credential_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to revalidate credential: {str(e)}"
        )
