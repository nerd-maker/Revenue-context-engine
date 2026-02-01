"""
Refresh materialized views job.

Run as cron job: 0 * * * * (hourly)
Refreshes CQRS read models for fast queries.
"""
from sqlalchemy import create_engine, text
from app.core.config import settings
import logging
import time
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("refresh_views")


def refresh_materialized_views():
    """
    Refresh all materialized views.
    Uses CONCURRENTLY to allow reads during refresh.
    """
    # Convert asyncpg URL to sync psycopg2 URL
    db_url = str(settings.DATABASE_URL).replace('+asyncpg', '')
    engine = create_engine(db_url)
    
    views = [
        'account_intent_scores',
        'high_intent_accounts'
    ]
    
    with engine.connect() as conn:
        for view in views:
            start = time.time()
            
            try:
                # CONCURRENTLY allows reads during refresh
                # Requires unique index on view
                conn.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}"))
                conn.commit()
                
                duration = time.time() - start
                logger.info(f"✓ Refreshed {view} in {duration:.2f}s")
                
            except Exception as e:
                logger.error(f"✗ Failed to refresh {view}: {e}", exc_info=True)
                conn.rollback()
    
    logger.info("Materialized view refresh completed")


if __name__ == "__main__":
    try:
        refresh_materialized_views()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
