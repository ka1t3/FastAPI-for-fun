"""
Security module for ChemAPI
Provides API key authentication and role-based access control
"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from typing import Optional, Dict
import os
from decouple import config

# Load API keys from environment or use defaults for development
# Format: key -> {name, role}
# In production, these should be stored securely and possibly hashed
DEFAULT_API_KEYS = {
    "chemapi-admin-key-2024": {"name": "admin", "role": "admin"},
    "chemapi-user1-key-2024": {"name": "user1", "role": "user"},
    "chemapi-user2-key-2024": {"name": "user2", "role": "user"},
}

# Load API keys from environment or use defaults
def load_api_keys() -> Dict[str, Dict[str, str]]:
    """Load API keys from environment or configuration"""
    # Try to load from environment variable
    env_keys = config('API_KEYS', default='')
    
    if env_keys:
        # Parse environment variable format: key:name:role,key:name:role
        keys = {}
        for key_entry in env_keys.split(','):
            parts = key_entry.strip().split(':')
            if len(parts) == 3:
                key, name, role = parts
                keys[key] = {"name": name, "role": role}
        return keys if keys else DEFAULT_API_KEYS
    
    return DEFAULT_API_KEYS

# Load valid API keys
VALID_API_KEYS = load_api_keys()

# API Key header configuration
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: Optional[str] = Security(api_key_header)) -> Dict[str, str]:
    """
    Validate API key from header
    Returns user information if valid
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required. Please provide X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
    
    return VALID_API_KEYS[api_key]

async def require_admin(user: Dict[str, str] = Security(get_api_key)) -> Dict[str, str]:
    """
    Require admin role for certain operations
    Use this dependency for endpoints that modify data
    """
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for this operation",
        )
    return user

async def require_user(user: Dict[str, str] = Security(get_api_key)) -> Dict[str, str]:
    """
    Require any authenticated user (admin or regular user)
    Use this dependency for read-only endpoints
    """
    # Any valid API key is sufficient
    return user

# Optional: Simple in-memory rate limiter
from collections import defaultdict
from datetime import datetime
import time

class SimpleRateLimiter:
    """Simple in-memory rate limiter per API key"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def check_rate_limit(self, key: str) -> bool:
        """Check if the key has exceeded rate limit"""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key] 
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.requests[key]) >= self.requests_per_minute:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True

# Initialize rate limiter (optional - can be disabled)
rate_limiter = SimpleRateLimiter(requests_per_minute=60)

async def check_rate_limit(user: Dict[str, str] = Security(get_api_key)) -> Dict[str, str]:
    """
    Check rate limit for the authenticated user
    Optional: Can be added to any endpoint that needs rate limiting
    """
    key = user["name"]
    
    if not rate_limiter.check_rate_limit(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"},
        )
    
    return user