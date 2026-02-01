"""
Input Validation Middleware

Protects against SQL injection, XSS attacks, and oversized requests.
"""
try:
    from fastapi import Request, HTTPException
except ImportError:
    Request = HTTPException = None
from starlette.middleware.base import BaseHTTPMiddleware
import re
import logging

logger = logging.getLogger("input_validation")

# Maximum request size: 10MB
MAX_REQUEST_SIZE = 10 * 1024 * 1024

# SQL Injection patterns
# These patterns detect common SQL injection attempts
SQL_INJECTION_PATTERNS = [
    r"(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bCREATE\b|\bALTER\b)",
    r"(\bOR\b\s+\d+\s*=\s*\d+)",  # OR 1=1
    r"(--|;|\/\*|\*\/)",  # SQL comments and statement terminators
    r"\bUNION\b.*\bSELECT\b",  # UNION SELECT attacks
    r"(\bEXEC\b|\bEXECUTE\b)",  # Command execution
    r"'.*(\bOR\b|\bAND\b).*'",  # Quote-based injection
]

# XSS (Cross-Site Scripting) patterns
# These patterns detect common XSS attack vectors
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",  # Script tags
    r"javascript:",  # JavaScript protocol
    r"on\w+\s*=",  # Event handlers (onclick, onerror, etc.)
    r"<iframe[^>]*>",  # Iframe tags
    r"<object[^>]*>",  # Object tags
    r"<embed[^>]*>",  # Embed tags
    r"<img[^>]*onerror",  # Image with onerror
]

# Compile patterns for better performance
SQL_PATTERNS_COMPILED = [re.compile(pattern, re.IGNORECASE) for pattern in SQL_INJECTION_PATTERNS]
XSS_PATTERNS_COMPILED = [re.compile(pattern, re.IGNORECASE) for pattern in XSS_PATTERNS]


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that validates input to protect against SQL injection, XSS, and oversized requests.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Validate request before processing.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain
            
        Returns:
            Response from next middleware or 400 error if validation fails
        """
        try:
            # Check request size
            content_length = request.headers.get('content-length')
            if content_length and int(content_length) > MAX_REQUEST_SIZE:
                logger.warning(
                    f"Request size too large: {content_length} bytes from {request.client.host}"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Request size too large. Maximum allowed: {MAX_REQUEST_SIZE / 1024 / 1024}MB"
                )
            
            # Check query parameters for dangerous patterns
            query_string = str(request.url.query)
            if query_string:
                self._validate_input(query_string, "query parameters", request)
            
            # Check request body for JSON requests
            if request.headers.get('content-type', '').startswith('application/json'):
                # Read body once and store it
                body = await request.body()
                if body:
                    body_str = body.decode('utf-8')
                    self._validate_input(body_str, "request body", request)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in input validation: {e}")
            # Don't block request on validation errors, just log
            pass
        
        return await call_next(request)
    
    def _validate_input(self, input_str: str, input_type: str, request: Request):
        """
        Validate input string against SQL injection and XSS patterns.
        
        Args:
            input_str: Input string to validate
            input_type: Type of input (for logging)
            request: Request object (for logging)
            
        Raises:
            HTTPException: If dangerous pattern is detected
        """
        # Check for SQL injection patterns
        for pattern in SQL_PATTERNS_COMPILED:
            if pattern.search(input_str):
                logger.warning(
                    f"SQL injection attempt detected in {input_type} from {request.client.host}: "
                    f"Pattern: {pattern.pattern}, Path: {request.url.path}"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid input detected in {input_type}. SQL-like patterns are not allowed."
                )
        
        # Check for XSS patterns
        for pattern in XSS_PATTERNS_COMPILED:
            if pattern.search(input_str):
                logger.warning(
                    f"XSS attempt detected in {input_type} from {request.client.host}: "
                    f"Pattern: {pattern.pattern}, Path: {request.url.path}"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid input detected in {input_type}. HTML/JavaScript patterns are not allowed."
                )


class RequestValidationMiddleware(InputValidationMiddleware):
    """
    Alias for InputValidationMiddleware to maintain backward compatibility.
    """
    pass
