#!/bin/bash

#############################################################################
# PostgreSQL Database Backup Script
#
# This script creates automated backups of the PostgreSQL database using
# pg_dump with custom format and gzip compression.
#
# Features:
# - Custom format backup for flexibility
# - Gzip compression to save space
# - Timestamped filenames
# - Automatic cleanup of old backups (30+ days)
# - Environment variable configuration
# - Error handling and logging
#
# Usage:
#   ./backup_database.sh
#
# Crontab Setup (daily at 2 AM):
#   0 2 * * * /path/to/scripts/backup_database.sh >> /var/log/db_backup.log 2>&1
#
# Environment Variables Required:
#   DATABASE_URL or individual components:
#   - PGHOST (default: localhost)
#   - PGPORT (default: 5432)
#   - PGDATABASE (required)
#   - PGUSER (required)
#   - PGPASSWORD (required)
#
#############################################################################

# Exit on any error
set -e

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Parse DATABASE_URL if provided (format: postgresql://user:pass@host:port/dbname)
if [ -n "$DATABASE_URL" ]; then
    # Extract components from DATABASE_URL
    # Remove postgresql:// prefix
    DB_URL="${DATABASE_URL#postgresql://}"
    
    # Extract user:password
    USER_PASS="${DB_URL%%@*}"
    export PGUSER="${USER_PASS%%:*}"
    export PGPASSWORD="${USER_PASS#*:}"
    
    # Extract host:port/database
    HOST_DB="${DB_URL#*@}"
    HOST_PORT="${HOST_DB%%/*}"
    export PGHOST="${HOST_PORT%%:*}"
    export PGPORT="${HOST_PORT#*:}"
    export PGDATABASE="${HOST_DB#*/}"
else
    # Use individual environment variables
    export PGHOST="${PGHOST:-localhost}"
    export PGPORT="${PGPORT:-5432}"
    
    if [ -z "$PGDATABASE" ] || [ -z "$PGUSER" ] || [ -z "$PGPASSWORD" ]; then
        echo "ERROR: DATABASE_URL or PGDATABASE, PGUSER, and PGPASSWORD must be set"
        exit 1
    fi
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup filename
BACKUP_FILE="$BACKUP_DIR/${PGDATABASE}_${TIMESTAMP}.backup"
COMPRESSED_FILE="${BACKUP_FILE}.gz"

echo "=========================================="
echo "PostgreSQL Backup Script"
echo "=========================================="
echo "Database: $PGDATABASE"
echo "Host: $PGHOST:$PGPORT"
echo "User: $PGUSER"
echo "Backup file: $COMPRESSED_FILE"
echo "Timestamp: $TIMESTAMP"
echo "=========================================="

# Create backup using pg_dump with custom format
echo "Starting backup..."
pg_dump \
    --host="$PGHOST" \
    --port="$PGPORT" \
    --username="$PGUSER" \
    --dbname="$PGDATABASE" \
    --format=custom \
    --file="$BACKUP_FILE" \
    --verbose

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "✓ Backup created successfully: $BACKUP_FILE"
else
    echo "✗ ERROR: Backup failed"
    exit 1
fi

# Compress the backup
echo "Compressing backup..."
gzip "$BACKUP_FILE"

# Check if compression was successful
if [ $? -eq 0 ]; then
    echo "✓ Backup compressed successfully: $COMPRESSED_FILE"
    
    # Get file size
    FILE_SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)
    echo "  Compressed size: $FILE_SIZE"
else
    echo "✗ ERROR: Compression failed"
    exit 1
fi

# Clean up old backups (older than RETENTION_DAYS)
echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
DELETED_COUNT=$(find "$BACKUP_DIR" -name "${PGDATABASE}_*.backup.gz" -type f -mtime +$RETENTION_DAYS -delete -print | wc -l)

if [ "$DELETED_COUNT" -gt 0 ]; then
    echo "✓ Deleted $DELETED_COUNT old backup(s)"
else
    echo "  No old backups to delete"
fi

# List current backups
echo ""
echo "Current backups:"
ls -lh "$BACKUP_DIR"/${PGDATABASE}_*.backup.gz | tail -n 5

echo ""
echo "=========================================="
echo "✓ Backup completed successfully!"
echo "=========================================="
echo "Backup file: $COMPRESSED_FILE"
echo "Size: $FILE_SIZE"
echo "Timestamp: $TIMESTAMP"
echo "=========================================="

# Exit successfully
exit 0

#############################################################################
# CRONTAB SETUP INSTRUCTIONS
#############################################################################
#
# To schedule this script to run daily at 2 AM:
#
# 1. Make the script executable:
#    chmod +x /path/to/scripts/backup_database.sh
#
# 2. Edit your crontab:
#    crontab -e
#
# 3. Add this line (adjust path as needed):
#    0 2 * * * /path/to/scripts/backup_database.sh >> /var/log/db_backup.log 2>&1
#
# 4. Verify the crontab entry:
#    crontab -l
#
# 5. Ensure environment variables are available to cron:
#    - Option 1: Source a .env file in the script
#    - Option 2: Set variables in crontab:
#      0 2 * * * export $(cat /path/to/.env | xargs) && /path/to/scripts/backup_database.sh
#
# 6. Monitor backup logs:
#    tail -f /var/log/db_backup.log
#
#############################################################################
# RESTORE INSTRUCTIONS
#############################################################################
#
# To restore from a backup:
#
# 1. Decompress the backup:
#    gunzip /backups/revenue_context_20260201_020000.backup.gz
#
# 2. Restore using pg_restore:
#    pg_restore \
#      --host=localhost \
#      --port=5432 \
#      --username=postgres \
#      --dbname=revenue_context \
#      --clean \
#      --if-exists \
#      --verbose \
#      /backups/revenue_context_20260201_020000.backup
#
# 3. Or restore to a new database:
#    createdb revenue_context_restored
#    pg_restore \
#      --host=localhost \
#      --port=5432 \
#      --username=postgres \
#      --dbname=revenue_context_restored \
#      --verbose \
#      /backups/revenue_context_20260201_020000.backup
#
#############################################################################
