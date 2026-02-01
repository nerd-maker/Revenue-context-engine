"""
Create next month's audit log partition.

This script should be run as a cron job on the 1st of each month:
    0 0 1 * * python scripts/create_audit_partitions.py

It creates the partition for the upcoming month to ensure continuous
audit log storage without manual intervention.
"""
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, text
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("partition_creator")


def create_next_partition():
    """
    Create partition for next month if it doesn't already exist.
    """
    engine = create_engine(str(settings.DATABASE_URL).replace('+asyncpg', ''))
    
    # Calculate next month
    next_month = datetime.now() + relativedelta(months=1)
    partition_name = f"audit_logs_{next_month.strftime('%Y_%m')}"
    start_date = next_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + relativedelta(months=1)
    
    logger.info(f"Checking partition: {partition_name}")
    logger.info(f"Date range: {start_date} to {end_date}")
    
    with engine.connect() as conn:
        # Check if partition already exists
        result = conn.execute(text(f"""
            SELECT 1 FROM pg_tables 
            WHERE tablename = '{partition_name}';
        """))
        
        if result.fetchone():
            logger.info(f"Partition {partition_name} already exists - skipping")
            return
        
        # Create partition
        logger.info(f"Creating partition: {partition_name}")
        conn.execute(text(f"""
            CREATE TABLE {partition_name} PARTITION OF audit_logs
                FOR VALUES FROM ('{start_date.isoformat()}') TO ('{end_date.isoformat()}');
        """))
        conn.commit()
        
        logger.info(f"✓ Successfully created partition: {partition_name}")


if __name__ == "__main__":
    try:
        create_next_partition()
        logger.info("Partition creation completed successfully")
    except Exception as e:
        logger.error(f"Failed to create partition: {e}", exc_info=True)
        sys.exit(1)
