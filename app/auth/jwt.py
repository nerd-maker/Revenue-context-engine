"""
JWT Authentication Module

Implements secure JWT token generation and validation with:
- Dual token system (access tokens: 15min, refresh tokens: 7 days)
- Unique token IDs (jti) for revocation support
- Strict secret validation (>= 32 characters, no defaults)
- Token type validation
- Comprehensive error handling
"""
import jwt
try:
    from fastapi import HTTPException, Request
except ImportError:
    HTTPException = Request = None
from datetime import datetime, timedelta
import os
import uuid

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRY_MINUTES = 15
REFRESH_TOKEN_EXPIRY_DAYS = 7

# Token types
TOKEN_TYPE_ACCESS = 'access'
TOKEN_TYPE_REFRESH = 'refresh'


def validate_jwt_secret():
    """
    Validate JWT_SECRET on startup.
    
    Raises:
        ValueError: If JWT_SECRET is not set or is too short
    """
    if not JWT_SECRET:
        raise ValueError(
            "JWT_SECRET environment variable must be set. "
            "Generate a secure secret with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    
    if len(JWT_SECRET) < 32:
        raise ValueError(
            f"JWT_SECRET must be at least 32 characters long (current length: {len(JWT_SECRET)}). "
            "Generate a secure secret with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )


def create_access_token(tenant_id: str, user_id: str) -> str:
    """
    Create an access token with 15-minute expiry.
    
    Args:
        tenant_id: Tenant identifier
        user_id: User identifier
        
    Returns:
        Encoded JWT access token
    """
    payload = {
        'tenant_id': tenant_id,
        'user_id': user_id,
        'token_type': TOKEN_TYPE_ACCESS,
        'jti': str(uuid.uuid4()),  # Unique token ID for revocation
        'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(tenant_id: str, user_id: str) -> str:
    """
    Create a refresh token with 7-day expiry.
    
    Args:
        tenant_id: Tenant identifier
        user_id: User identifier
        
    Returns:
        Encoded JWT refresh token
    """
    payload = {
        'tenant_id': tenant_id,
        'user_id': user_id,
        'token_type': TOKEN_TYPE_REFRESH,
        'jti': str(uuid.uuid4()),  # Unique token ID for revocation
        'exp': datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_jwt_token(tenant_id: str, user_id: str) -> dict:
    """
    Create both access and refresh tokens.
    
    Args:
        tenant_id: Tenant identifier
        user_id: User identifier
        
    Returns:
        Dictionary with access_token and refresh_token
    """
    return {
        'access_token': create_access_token(tenant_id, user_id),
        'refresh_token': create_refresh_token(tenant_id, user_id),
        'token_type': 'bearer',
        'expires_in': ACCESS_TOKEN_EXPIRY_MINUTES * 60  # seconds
    }


def validate_token_type(payload: dict, expected_type: str):
    """
    Validate that token type matches expected type.
    
    Args:
        payload: Decoded JWT payload
        expected_type: Expected token type ('access' or 'refresh')
        
    Raises:
        HTTPException: If token type doesn't match expected type
    """
    token_type = payload.get('token_type')
    if token_type != expected_type:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token type. Expected '{expected_type}' token, got '{token_type}' token"
        )


def decode_jwt_token(token: str, expected_type: str = None) -> dict:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
        expected_type: Optional expected token type ('access' or 'refresh')
        
    Returns:
        Decoded payload dictionary
        
    Raises:
        HTTPException: If token is invalid, expired, or wrong type
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Validate token type if specified
        if expected_type:
            validate_token_type(payload, expected_type)
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail='Token has expired. Please obtain a new token using your refresh token.'
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=f'Invalid token: {str(e)}'
        )


def get_tenant_id_from_request(request: Request) -> str:
    """
    Extract and validate tenant ID from request Authorization header.
    
    Only accepts access tokens (not refresh tokens).
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Tenant ID from token
        
    Raises:
        HTTPException: If authorization header is missing, invalid, or token is wrong type
    """
    auth = request.headers.get('Authorization')
    
    if not auth:
        raise HTTPException(
            status_code=401,
            detail='Missing Authorization header. Include header: Authorization: Bearer <token>'
        )
    
    if not auth.startswith('Bearer '):
        raise HTTPException(
            status_code=401,
            detail='Invalid Authorization header format. Use: Authorization: Bearer <token>'
        )
    
    token = auth.split(' ')[1]
    
    # Validate this is an access token (not refresh token)
    payload = decode_jwt_token(token, expected_type=TOKEN_TYPE_ACCESS)
    
    return payload['tenant_id']


def refresh_access_token(refresh_token: str) -> dict:
    """
    Generate new access token using refresh token.
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        Dictionary with new access_token
        
    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    # Validate this is a refresh token
    payload = decode_jwt_token(refresh_token, expected_type=TOKEN_TYPE_REFRESH)
    
    # Create new access token with same tenant_id and user_id
    access_token = create_access_token(
        tenant_id=payload['tenant_id'],
        user_id=payload['user_id']
    )
    
    return {
        'access_token': access_token,
        'token_type': 'bearer',
        'expires_in': ACCESS_TOKEN_EXPIRY_MINUTES * 60
    }


# Validate JWT_SECRET on module import
validate_jwt_secret()
