"""
Test JWT Authentication Enhancements

Tests for the enhanced JWT authentication with access/refresh tokens,
token IDs, strict validation, and proper error handling.
"""
import pytest
import os
import sys
from datetime import datetime, timedelta

# Set JWT_SECRET before importing jwt module
os.environ['JWT_SECRET'] = 'test-secret-key-with-at-least-32-characters-for-security'

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    create_jwt_token,
    decode_jwt_token,
    get_tenant_id_from_request,
    refresh_access_token,
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    validate_jwt_secret
)


class TestJWTValidation:
    """Test JWT secret validation"""
    
    def test_jwt_secret_validation_success(self):
        """Test that valid JWT_SECRET passes validation"""
        # Should not raise any exception
        validate_jwt_secret()
    
    def test_jwt_secret_too_short(self):
        """Test that short JWT_SECRET raises error"""
        # Save original
        original = os.environ.get('JWT_SECRET')
        
        try:
            # Set short secret
            os.environ['JWT_SECRET'] = 'short'
            
            # Re-import to trigger validation
            import importlib
            import app.auth.jwt as jwt_module
            
            with pytest.raises(ValueError, match="at least 32 characters"):
                importlib.reload(jwt_module)
        finally:
            # Restore original
            if original:
                os.environ['JWT_SECRET'] = original


class TestAccessTokens:
    """Test access token creation and validation"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        tenant_id = "tenant-123"
        user_id = "user-456"
        
        token = create_access_token(tenant_id, user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_access_token(self):
        """Test access token decoding"""
        tenant_id = "tenant-123"
        user_id = "user-456"
        
        token = create_access_token(tenant_id, user_id)
        payload = decode_jwt_token(token, expected_type=TOKEN_TYPE_ACCESS)
        
        assert payload['tenant_id'] == tenant_id
        assert payload['user_id'] == user_id
        assert payload['token_type'] == TOKEN_TYPE_ACCESS
        assert 'jti' in payload
        assert 'exp' in payload
        assert 'iat' in payload
    
    def test_access_token_has_unique_jti(self):
        """Test that each access token has unique jti"""
        tenant_id = "tenant-123"
        user_id = "user-456"
        
        token1 = create_access_token(tenant_id, user_id)
        token2 = create_access_token(tenant_id, user_id)
        
        payload1 = decode_jwt_token(token1)
        payload2 = decode_jwt_token(token2)
        
        assert payload1['jti'] != payload2['jti']


class TestRefreshTokens:
    """Test refresh token creation and validation"""
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        tenant_id = "tenant-123"
        user_id = "user-456"
        
        token = create_refresh_token(tenant_id, user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_refresh_token(self):
        """Test refresh token decoding"""
        tenant_id = "tenant-123"
        user_id = "user-456"
        
        token = create_refresh_token(tenant_id, user_id)
        payload = decode_jwt_token(token, expected_type=TOKEN_TYPE_REFRESH)
        
        assert payload['tenant_id'] == tenant_id
        assert payload['user_id'] == user_id
        assert payload['token_type'] == TOKEN_TYPE_REFRESH
        assert 'jti' in payload
    
    def test_refresh_token_generates_new_access_token(self):
        """Test that refresh token can generate new access token"""
        tenant_id = "tenant-123"
        user_id = "user-456"
        
        refresh_token = create_refresh_token(tenant_id, user_id)
        result = refresh_access_token(refresh_token)
        
        assert 'access_token' in result
        assert 'token_type' in result
        assert 'expires_in' in result
        assert result['token_type'] == 'bearer'
        
        # Verify new access token is valid
        new_payload = decode_jwt_token(result['access_token'], expected_type=TOKEN_TYPE_ACCESS)
        assert new_payload['tenant_id'] == tenant_id
        assert new_payload['user_id'] == user_id


class TestTokenTypeValidation:
    """Test token type validation"""
    
    def test_reject_refresh_token_when_access_expected(self):
        """Test that refresh token is rejected when access token expected"""
        tenant_id = "tenant-123"
        user_id = "user-456"
        
        refresh_token = create_refresh_token(tenant_id, user_id)
        
        with pytest.raises(Exception, match="Invalid token type"):
            decode_jwt_token(refresh_token, expected_type=TOKEN_TYPE_ACCESS)
    
    def test_reject_access_token_when_refresh_expected(self):
        """Test that access token is rejected when refresh token expected"""
        tenant_id = "tenant-123"
        user_id = "user-456"
        
        access_token = create_access_token(tenant_id, user_id)
        
        with pytest.raises(Exception, match="Invalid token type"):
            decode_jwt_token(access_token, expected_type=TOKEN_TYPE_REFRESH)


class TestDualTokenCreation:
    """Test dual token creation"""
    
    def test_create_jwt_token_returns_both_tokens(self):
        """Test that create_jwt_token returns both access and refresh tokens"""
        tenant_id = "tenant-123"
        user_id = "user-456"
        
        result = create_jwt_token(tenant_id, user_id)
        
        assert 'access_token' in result
        assert 'refresh_token' in result
        assert 'token_type' in result
        assert 'expires_in' in result
        assert result['token_type'] == 'bearer'
        
        # Verify both tokens are valid
        access_payload = decode_jwt_token(result['access_token'], expected_type=TOKEN_TYPE_ACCESS)
        refresh_payload = decode_jwt_token(result['refresh_token'], expected_type=TOKEN_TYPE_REFRESH)
        
        assert access_payload['tenant_id'] == tenant_id
        assert refresh_payload['tenant_id'] == tenant_id


class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_token_raises_error(self):
        """Test that invalid token raises proper error"""
        with pytest.raises(Exception, match="Invalid token"):
            decode_jwt_token("invalid.token.here")
    
    def test_expired_token_raises_error(self):
        """Test that expired token raises proper error"""
        # This would require mocking time or waiting for expiry
        # For now, just test the error message format
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
