"""
Token Encryption Module

Implements secure encryption with:
- Strict Fernet key validation
- Key rotation support (primary/secondary keys)
- MultiFernet for seamless key rotation
- Comprehensive error handling
"""
from cryptography.fernet import Fernet, MultiFernet, InvalidToken
import os
import base64
import logging

logger = logging.getLogger("encryption")


def validate_fernet_key(key: str, key_name: str) -> bytes:
    """
    Validate that a key is a valid Fernet key.
    
    Args:
        key: Key string to validate
        key_name: Name of the key (for error messages)
        
    Returns:
        Key as bytes
        
    Raises:
        ValueError: If key is invalid
    """
    if not key:
        raise ValueError(
            f"{key_name} is not set. "
            "Generate a valid Fernet key using:\n"
            "  python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    
    try:
        # Fernet keys are 44 characters (32 bytes base64 encoded)
        key_bytes = key.encode() if isinstance(key, str) else key
        
        # Validate by trying to create a Fernet instance
        Fernet(key_bytes)
        
        return key_bytes
        
    except Exception as e:
        raise ValueError(
            f"{key_name} is not a valid Fernet key: {str(e)}\n"
            "Generate a valid Fernet key using:\n"
            "  python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'\n"
            f"Expected format: 44 characters, base64-encoded (e.g., '{Fernet.generate_key().decode()}')"
        )


class TokenEncryption:
    """
    Token encryption with key rotation support.
    
    Supports primary and secondary encryption keys for seamless key rotation:
    - Encrypts with primary key
    - Decrypts with both keys (tries primary first, then secondary)
    """
    
    def __init__(self):
        """
        Initialize encryption with key validation and rotation support.
        
        Environment Variables:
            ENCRYPTION_KEY_PRIMARY: Primary encryption key (required)
            ENCRYPTION_KEY_SECONDARY: Secondary encryption key (optional, for rotation)
            ENCRYPTION_KEY: Legacy single key (deprecated, use ENCRYPTION_KEY_PRIMARY)
        """
        # Support both new (PRIMARY/SECONDARY) and legacy (ENCRYPTION_KEY) formats
        primary_key = os.getenv('ENCRYPTION_KEY_PRIMARY') or os.getenv('ENCRYPTION_KEY')
        secondary_key = os.getenv('ENCRYPTION_KEY_SECONDARY')
        
        # Validate primary key
        primary_key_bytes = validate_fernet_key(primary_key, 'ENCRYPTION_KEY_PRIMARY')
        
        # Setup encryption
        if secondary_key:
            # Key rotation mode: use MultiFernet with both keys
            secondary_key_bytes = validate_fernet_key(secondary_key, 'ENCRYPTION_KEY_SECONDARY')
            
            # MultiFernet tries keys in order: primary first, then secondary
            self.cipher = MultiFernet([
                Fernet(primary_key_bytes),
                Fernet(secondary_key_bytes)
            ])
            
            logger.info("Encryption initialized with key rotation support (primary + secondary keys)")
        else:
            # Single key mode
            self.cipher = Fernet(primary_key_bytes)
            logger.info("Encryption initialized with single key")
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext and return base64 string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
            
        Raises:
            ValueError: If plaintext is empty
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")
        
        try:
            encrypted_bytes = self.cipher.encrypt(plaintext.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Encryption failed: {str(e)}")
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext from base64 string.
        
        When using key rotation (MultiFernet), this will try:
        1. Primary key first
        2. Secondary key if primary fails
        
        Args:
            ciphertext: Encrypted string (base64 encoded)
            
        Returns:
            Decrypted plaintext string
            
        Raises:
            ValueError: If ciphertext is empty or decryption fails
        """
        if not ciphertext:
            raise ValueError("Cannot decrypt empty string")
        
        try:
            decrypted_bytes = self.cipher.decrypt(ciphertext.encode())
            return decrypted_bytes.decode()
        except InvalidToken:
            raise ValueError(
                "Decryption failed: Invalid token or wrong encryption key. "
                "If you recently rotated keys, ensure ENCRYPTION_KEY_SECONDARY is set to the old key."
            )
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Decryption failed: {str(e)}")


# Initialize global encryptor instance
# This will validate keys on module import
encryptor = TokenEncryption()
