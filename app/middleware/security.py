"""
Secure CORS Configuration

Implements strict CORS policy with environment-based configuration.
"""
from fastapi.middleware.cors import CORSMiddleware
try:
    from fastapi import FastAPI
except ImportError:
    FastAPI = None
from app.core.config import settings
import logging

logger = logging.getLogger("security")


def add_cors(app: FastAPI):
    """
    Add CORS middleware with secure configuration.
    
    Configuration:
    - ALLOWED_ORIGINS: Comma-separated list of allowed origins (required in production)
    - Only allows specific HTTP methods: GET, POST, PUT, DELETE
    - Only allows specific headers: Authorization, Content-Type
    - Enables credentials for cookie support
    - Sets preflight cache to 600 seconds
    
    Environment Variables:
        ALLOWED_ORIGINS: Comma-separated list of allowed origins
            Example: "https://app.example.com,https://admin.example.com"
            In development: Can use "*" but not recommended
            In production: Must be set to specific origins
    
    Raises:
        ValueError: If ALLOWED_ORIGINS is not set in production environment
    """
    # Get allowed origins from environment
    allowed_origins_str = getattr(settings, 'ALLOWED_ORIGINS', None)
    
    # Strict validation in production
    if settings.ENV == 'production':
        if not allowed_origins_str:
            raise ValueError(
                "ALLOWED_ORIGINS environment variable must be set in production. "
                "Example: ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com"
            )
        
        if allowed_origins_str == "*":
            raise ValueError(
                "ALLOWED_ORIGINS cannot be '*' in production. "
                "Specify explicit origins: ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com"
            )
    
    # Parse allowed origins
    if allowed_origins_str:
        if allowed_origins_str == "*":
            allowed_origins = ["*"]
            logger.warning(
                "CORS configured with wildcard origin '*'. "
                "This is insecure and should only be used in development."
            )
        else:
            allowed_origins = [
                origin.strip() 
                for origin in allowed_origins_str.split(',')
                if origin.strip()
            ]
            logger.info(f"CORS configured with {len(allowed_origins)} allowed origins")
    else:
        # Default for development only
        if settings.ENV == 'production':
            raise ValueError("ALLOWED_ORIGINS must be set in production")
        
        allowed_origins = ["http://localhost:3000", "http://localhost:8000"]
        logger.warning(
            f"ALLOWED_ORIGINS not set, using development defaults: {allowed_origins}"
        )
    
    # Allowed HTTP methods (restrict to only necessary methods)
    allowed_methods = ["GET", "POST", "PUT", "DELETE"]
    
    # Allowed headers (restrict to only necessary headers)
    allowed_headers = ["Authorization", "Content-Type"]
    
    # Add CORS middleware with strict configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,  # Allow cookies and authorization headers
        allow_methods=allowed_methods,  # Only specific methods
        allow_headers=allowed_headers,  # Only specific headers
        max_age=600,  # Cache preflight requests for 10 minutes
    )
    
    logger.info(
        f"CORS middleware configured: "
        f"origins={len(allowed_origins)}, "
        f"methods={allowed_methods}, "
        f"headers={allowed_headers}, "
        f"credentials=True"
    )
