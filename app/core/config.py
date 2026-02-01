import os
from pydantic_settings import BaseSettings
from pydantic import field_validator, computed_field
from dotenv import load_dotenv
import pathlib
import re
from cryptography.fernet import Fernet

# Always load .env for local/dev/test
load_dotenv(dotenv_path=pathlib.Path(__file__).parent.parent / '.env', override=True)


class Settings(BaseSettings):
    """
    Application settings with strict validation.
    
    All security-critical settings are validated on initialization.
    """
    # Environment
    ENV: str = os.getenv('ENV', 'development')

    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', '')
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv('KAFKA_BOOTSTRAP_SERVERS', '')

    # External APIs (optional in dev/test)
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    OUTREACH_API_KEY: str = os.getenv('OUTREACH_API_KEY', '')
    CLEARBIT_API_KEY: str = os.getenv('CLEARBIT_API_KEY', '')
    SALESFORCE_CLIENT_ID: str = os.getenv('SALESFORCE_CLIENT_ID', '')
    SALESFORCE_CLIENT_SECRET: str = os.getenv('SALESFORCE_CLIENT_SECRET', '')

    # Security
    ENCRYPTION_KEY: str = os.getenv('ENCRYPTION_KEY', '')
    ENCRYPTION_KEY_PRIMARY: str = os.getenv('ENCRYPTION_KEY_PRIMARY', '')
    ENCRYPTION_KEY_SECONDARY: str = os.getenv('ENCRYPTION_KEY_SECONDARY', '')
    JWT_SECRET: str = os.getenv('JWT_SECRET', '')
    
    # CORS
    ALLOWED_ORIGINS: str = os.getenv('ALLOWED_ORIGINS', '')

    # Feature flags
    EMAIL_DAILY_LIMIT_PER_ACCOUNT: int = int(os.getenv('EMAIL_DAILY_LIMIT_PER_ACCOUNT', '1'))
    HIGH_INTENT_THRESHOLD: int = int(os.getenv('HIGH_INTENT_THRESHOLD', '75'))
    EXECUTION_MODE: str = os.getenv('EXECUTION_MODE', 'laboratory')

    # Budget controls
    ENRICHMENT_BUDGET_PER_ACCOUNT: float = float(os.getenv('ENRICHMENT_BUDGET_PER_ACCOUNT', '0.50'))
    ENRICHMENT_BUDGET_PERIOD: str = os.getenv('ENRICHMENT_BUDGET_PERIOD', 'monthly')
    LAB_SIGNAL_REPLAY_DAYS: int = int(os.getenv('LAB_SIGNAL_REPLAY_DAYS', '30'))

    @field_validator('JWT_SECRET')
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """
        Validate JWT_SECRET is set and meets minimum length requirements.
        
        Requirements:
        - Must be set (no default allowed)
        - Must be at least 32 characters long
        
        Raises:
            ValueError: If JWT_SECRET is invalid
        """
        if not v:
            raise ValueError(
                "JWT_SECRET environment variable must be set. "
                "Generate a secure secret with:\n"
                "  python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        if len(v) < 32:
            raise ValueError(
                f"JWT_SECRET must be at least 32 characters long (current: {len(v)}). "
                "Generate a secure secret with:\n"
                "  python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        
        return v

    @field_validator('ENCRYPTION_KEY', 'ENCRYPTION_KEY_PRIMARY')
    @classmethod
    def validate_encryption_key(cls, v: str, info) -> str:
        """
        Validate encryption key is a valid Fernet key.
        
        Requirements:
        - Must be 44 characters (32 bytes base64 encoded)
        - Must be valid base64
        - Must be a valid Fernet key
        
        Raises:
            ValueError: If encryption key is invalid
        """
        field_name = info.field_name
        
        # Skip validation for ENCRYPTION_KEY if ENCRYPTION_KEY_PRIMARY is set
        if field_name == 'ENCRYPTION_KEY' and os.getenv('ENCRYPTION_KEY_PRIMARY'):
            return v
        
        # ENCRYPTION_KEY_PRIMARY is required, ENCRYPTION_KEY is legacy fallback
        if field_name == 'ENCRYPTION_KEY_PRIMARY' and not v:
            # Check for legacy ENCRYPTION_KEY
            legacy_key = os.getenv('ENCRYPTION_KEY')
            if not legacy_key:
                raise ValueError(
                    "ENCRYPTION_KEY_PRIMARY (or legacy ENCRYPTION_KEY) must be set. "
                    "Generate a valid Fernet key with:\n"
                    "  python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
                )
            return legacy_key
        
        if v:
            try:
                # Validate it's a valid Fernet key
                Fernet(v.encode() if isinstance(v, str) else v)
            except Exception as e:
                raise ValueError(
                    f"{field_name} is not a valid Fernet key: {str(e)}\n"
                    "Generate a valid Fernet key with:\n"
                    "  python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'\n"
                    f"Expected format: 44 characters, base64-encoded (e.g., '{Fernet.generate_key().decode()}')"
                )
        
        return v

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """
        Validate DATABASE_URL is set.
        
        Raises:
            ValueError: If DATABASE_URL is not set
        """
        if not v:
            raise ValueError(
                "DATABASE_URL environment variable must be set. "
                "Example: postgresql+psycopg2://user:password@localhost:5432/dbname"
            )
        
        # Basic format validation
        if not v.startswith(('postgresql://', 'postgresql+psycopg2://', 'postgresql+asyncpg://')):
            raise ValueError(
                "DATABASE_URL must start with 'postgresql://', 'postgresql+psycopg2://', or 'postgresql+asyncpg://'. "
                f"Current value starts with: {v[:20]}..."
            )
        
        return v

    @computed_field
    @property
    def safe_database_url(self) -> str:
        """
        Return DATABASE_URL with password masked for logging.
        
        Example:
            postgresql://user:***@localhost:5432/dbname
        """
        if not self.DATABASE_URL:
            return ""
        
        # Regex to find password in URL
        # Matches: postgresql://user:password@host
        pattern = r'(postgresql[^:]*://[^:]+:)([^@]+)(@.+)'
        
        def mask_password(match):
            return f"{match.group(1)}***{match.group(3)}"
        
        return re.sub(pattern, mask_password, self.DATABASE_URL)

    @property
    def KAFKA_ENABLED(self) -> bool:
        """Check if Kafka is configured and should be used"""
        return bool(self.KAFKA_BOOTSTRAP_SERVERS and self.KAFKA_BOOTSTRAP_SERVERS != 'localhost:9092')

    def validate_production(self):
        """
        Validate production-specific requirements.
        
        In production, all security-critical settings must be set.
        
        Raises:
            ValueError: If any required production setting is missing
        """
        if self.ENV != 'production':
            return  # Skip validation in dev/test
        
        # Production requirements
        required = {
            'GEMINI_API_KEY': self.GEMINI_API_KEY,
            'ENCRYPTION_KEY_PRIMARY': self.ENCRYPTION_KEY_PRIMARY or self.ENCRYPTION_KEY,
            'JWT_SECRET': self.JWT_SECRET,
            'ALLOWED_ORIGINS': self.ALLOWED_ORIGINS,
        }
        
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(
                f"Production environment requires the following variables to be set: {', '.join(missing)}\n"
                "Please set these in your .env file or environment."
            )
        
        # JWT_SECRET and ENCRYPTION_KEY are already validated by field validators

    class Config:
        env_file = ".env"
        case_sensitive = True
        # Validate on initialization
        validate_assignment = True


# Create settings instance - validation happens automatically
try:
    settings = Settings()
except Exception as e:
    # Re-raise with helpful context
    raise ValueError(
        f"Configuration validation failed: {str(e)}\n\n"
        "Please check your .env file and ensure all required variables are set correctly."
    ) from e


# Only validate production requirements at application startup, not at import
def validate_settings():
    """
    Validate settings at application startup.
    
    Call this in your FastAPI startup event:
        @app.on_event("startup")
        async def startup_event():
            validate_settings()
    """
    settings.validate_production()
