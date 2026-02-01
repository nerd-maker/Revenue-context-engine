"""
Secret Rotation Script

Rotates database passwords, encryption keys, and API keys.
Run quarterly via cron: 0 0 1 */3 *
"""
import boto3
from datetime import datetime
import logging
import sys
from cryptography.fernet import Fernet
import secrets

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("secret_rotation")


def get_account_id():
    """Get AWS account ID dynamically"""
    sts_client = boto3.client('sts')
    return sts_client.get_caller_identity()['Account']


def rotate_database_password(secret_arn: str, environment: str):
    """
    Rotate RDS password via Secrets Manager.
    
    Args:
        secret_arn: Secrets Manager ARN for database credentials
        environment: Environment name (production, staging)
    """
    secrets_client = boto3.client('secretsmanager')
    account_id = get_account_id()
    
    try:
        # Trigger rotation
        response = secrets_client.rotate_secret(
            SecretId=secret_arn,
            RotationLambdaARN=f'arn:aws:lambda:us-east-1:{account_id}:function:{environment}-rotate-rds-password'
        )
        
        logger.info(f"Database password rotation initiated: {response['VersionId']}")
        return response
    except Exception as e:
        logger.error(f"Failed to rotate database password: {e}", exc_info=True)
        raise


def rotate_encryption_key(environment: str):
    """
    Generate new encryption key and store in Secrets Manager.
    
    Note: Requires application restart or key versioning support.
    
    Args:
        environment: Environment name (production, staging)
    """
    new_key = Fernet.generate_key().decode()
    
    secrets_client = boto3.client('secretsmanager')
    secret_name = f'{environment}/revenue-context/encryption-key'
    
    try:
        secrets_client.put_secret_value(
            SecretId=secret_name,
            SecretString=new_key,
            VersionStages=['AWSCURRENT']
        )
        
        logger.info(f"Encryption key rotated for {environment}")
        logger.warning("Application restart required to use new encryption key")
        return new_key
    except Exception as e:
        logger.error(f"Failed to rotate encryption key: {e}", exc_info=True)
        raise


def rotate_api_keys(environment: str):
    """
    Rotate application API keys.
    
    Args:
        environment: Environment name (production, staging)
    """
    new_key = secrets.token_urlsafe(32)
    
    secrets_client = boto3.client('secretsmanager')
    secret_name = f'{environment}/revenue-context/api-key'
    
    try:
        secrets_client.put_secret_value(
            SecretId=secret_name,
            SecretString=new_key,
            VersionStages=['AWSCURRENT']
        )
        
        logger.info(f"API key rotated for {environment}")
        
        # Notify via SNS
        account_id = get_account_id()
        sns_client = boto3.client('sns')
        topic_arn = f'arn:aws:sns:us-east-1:{account_id}:{environment}-revenue-context-alerts'
        
        sns_client.publish(
            TopicArn=topic_arn,
            Subject=f'API Key Rotated - {environment}',
            Message=f'New API key generated at {datetime.now().isoformat()}\n\nEnvironment: {environment}'
        )
        
        return new_key
    except Exception as e:
        logger.error(f"Failed to rotate API key: {e}", exc_info=True)
        raise


def rotate_redis_auth_token(environment: str):
    """
    Rotate Redis AUTH token.
    
    Note: Requires ElastiCache cluster restart.
    
    Args:
        environment: Environment name (production, staging)
    """
    new_token = secrets.token_urlsafe(32)
    
    secrets_client = boto3.client('secretsmanager')
    secret_name = f'{environment}/revenue-context/redis-auth'
    
    try:
        # Get current secret
        current_secret = secrets_client.get_secret_value(SecretId=secret_name)
        import json
        secret_data = json.loads(current_secret['SecretString'])
        
        # Update auth token
        secret_data['auth_token'] = new_token
        
        secrets_client.put_secret_value(
            SecretId=secret_name,
            SecretString=json.dumps(secret_data),
            VersionStages=['AWSCURRENT']
        )
        
        logger.info(f"Redis AUTH token rotated for {environment}")
        logger.warning("ElastiCache cluster restart required to apply new AUTH token")
        return new_token
    except Exception as e:
        logger.error(f"Failed to rotate Redis AUTH token: {e}", exc_info=True)
        raise


def main():
    """Main rotation workflow"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Rotate secrets')
    parser.add_argument('--environment', required=True, choices=['production', 'staging'], help='Environment')
    parser.add_argument('--secrets', nargs='+', choices=['database', 'encryption', 'api', 'redis'], 
                        default=['api'], help='Secrets to rotate')
    
    args = parser.parse_args()
    
    logger.info(f"Starting secret rotation for {args.environment}")
    
    try:
        account_id = get_account_id()
        
        if 'database' in args.secrets:
            secret_arn = f'arn:aws:secretsmanager:us-east-1:{account_id}:secret:{args.environment}/revenue-context/db-credentials'
            rotate_database_password(secret_arn, args.environment)
        
        if 'encryption' in args.secrets:
            rotate_encryption_key(args.environment)
        
        if 'api' in args.secrets:
            rotate_api_keys(args.environment)
        
        if 'redis' in args.secrets:
            rotate_redis_auth_token(args.environment)
        
        logger.info("Secret rotation completed successfully")
    except Exception as e:
        logger.error(f"Secret rotation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
