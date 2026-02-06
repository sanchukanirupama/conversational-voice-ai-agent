import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt
from backend.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()

# Global store for active calls (in-memory for MVP)
active_calls: Dict[str, Dict[str, Any]] = {}


# Pydantic Models
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenVerifyResponse(BaseModel):
    valid: bool
    message: str


class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]


class ActiveCall(BaseModel):
    call_id: str
    customer_id: Optional[str]
    start_time: str
    duration_seconds: int
    is_verified: bool
    current_flow: Optional[str]
    message_count: int
    latest_message: Optional[str]


# JWT Token Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token and return payload"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Admin Routes
@router.post("/login", response_model=LoginResponse)
async def admin_login(credentials: LoginRequest):
    """Authenticate admin user and return JWT token"""
    # Verify credentials against environment variables
    if (credentials.username == settings.ADMIN_USERNAME and 
        credentials.password == settings.ADMIN_PASSWORD):
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": credentials.username, "role": "admin"},
            expires_delta=access_token_expires
        )
        
        return LoginResponse(access_token=access_token)
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/verify", response_model=TokenVerifyResponse)
async def verify_admin_token(payload: dict = Depends(verify_token)):
    """Verify if the provided JWT token is valid"""
    return TokenVerifyResponse(
        valid=True,
        message=f"Token valid for user: {payload.get('sub')}"
    )


@router.get("/config")
async def get_configuration(payload: dict = Depends(verify_token)):
    """Get the current unified configuration"""
    config_path = settings.PROMPTS_FILE
    
    if not os.path.exists(config_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration file not found"
        )
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading configuration: {str(e)}"
        )


@router.put("/config")
async def update_configuration(
    request: ConfigUpdateRequest,
    payload: dict = Depends(verify_token)
):
    """Update the unified configuration file"""
    config_path = settings.PROMPTS_FILE
    
    try:
        # Create backup of current config
        backup_path = config_path + ".backup"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                backup_data = f.read()
            with open(backup_path, 'w') as f:
                f.write(backup_data)
        
        # Write new configuration
        with open(config_path, 'w') as f:
            json.dump(request.config, f, indent=2)
        
        # Reload configuration in settings
        settings.reload_prompts()
        
        return {
            "success": True,
            "message": "Configuration updated successfully",
            "updated_by": payload.get('sub'),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Restore from backup if update failed
        if os.path.exists(backup_path):
            with open(backup_path, 'r') as f:
                backup_data = f.read()
            with open(config_path, 'w') as f:
                f.write(backup_data)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating configuration: {str(e)}"
        )


@router.get("/calls/live", response_model=List[ActiveCall])
async def get_live_calls(payload: dict = Depends(verify_token)):
    """Get list of currently active calls"""
    current_time = datetime.utcnow()
    live_calls = []
    
    for call_id, call_data in active_calls.items():
        start_time = datetime.fromisoformat(call_data['start_time'])
        duration = int((current_time - start_time).total_seconds())
        
        # Get latest message from transcript
        transcript = call_data.get('transcript', [])
        latest_message = transcript[-1] if transcript else None
        
        live_calls.append(ActiveCall(
            call_id=call_id,
            customer_id=call_data.get('customer_id'),
            start_time=call_data['start_time'],
            duration_seconds=duration,
            is_verified=call_data.get('is_verified', False),
            current_flow=call_data.get('current_flow'),
            message_count=len(transcript),
            latest_message=latest_message
        ))
    
    return live_calls


@router.get("/calls/{call_id}")
async def get_call_details(call_id: str, payload: dict = Depends(verify_token)):
    """Get detailed information about a specific call"""
    if call_id not in active_calls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )
    
    return active_calls[call_id]


@router.get("/customers")
async def get_customers(payload: dict = Depends(verify_token)):
    """Get list of all customers"""
    from backend.db.database import get_db
    from backend.db.models import Customer
    
    try:
        with get_db() as session:
            customers = session.query(Customer).all()
            return {
                "customers": [customer.to_dict() for customer in customers],
                "total": len(customers)
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching customers: {str(e)}"
        )

