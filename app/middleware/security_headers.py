"""
Security Headers Middleware

Adds security headers to all HTTP responses to protect against common web vulnerabilities.
"""
try:
    from fastapi import Request
except ImportError:
    Request = None
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger("security_headers")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds security headers to all responses.
    
    Headers added:
    - X-Content-Type-Options: nosniff - Prevents MIME type sniffing
    - X-Frame-Options: DENY - Prevents clickjacking attacks
    - X-XSS-Protection: 1; mode=block - Enables XSS filtering in browsers
    - Strict-Transport-Security: Forces HTTPS connections
    - Content-Security-Policy: Restricts resource loading to same origin
    - Referrer-Policy: Controls referrer information sent with requests
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and add security headers to response.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain
            
        Returns:
            Response with security headers added
        """
        response = await call_next(request)
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking by denying iframe embedding
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Enable XSS protection in browsers
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Force HTTPS for 1 year, including subdomains
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Restrict resource loading to same origin
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        
        # Control referrer information
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        logger.debug(f"Added security headers to response for {request.url.path}")
        
        return response
