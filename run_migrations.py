#!/usr/bin/env python
"""
Run Alembic migrations with proper error handling.
This script ensures DATABASE_URL is properly formatted for asyncpg.
"""
import os
import sys
import subprocess

def main():
    # Get DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Convert to asyncpg format
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    elif database_url.startswith('postgresql+psycopg2://'):
        database_url = database_url.replace('postgresql+psycopg2://', 'postgresql+asyncpg://', 1)
    
    # Set the converted URL
    os.environ['DATABASE_URL'] = database_url
    
    print(f"Running migrations with DATABASE_URL: {database_url.split('@')[0]}@...")
    
    # Run alembic upgrade
    result = subprocess.run(
        ['alembic', 'upgrade', 'head'],
        env=os.environ.copy()
    )
    
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()
