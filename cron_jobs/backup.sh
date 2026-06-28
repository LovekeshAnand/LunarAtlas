#!/usr/bin/env bash
# ==============================================================================
# LUNARATLAS DATABASE DAILY BACKUP AUTOMATION
# ==============================================================================
set -e

# Ensure DATABASE_URL is available
if [ -z "$DATABASE_URL" ]; then
    echo "[ERROR] DATABASE_URL is not set. Cannot run backup."
    exit 1
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/tmp/lunaratlas_backups"
BACKUP_FILE="${BACKUP_DIR}/lunaratlas_backup_${TIMESTAMP}.sql"
GZIP_FILE="${BACKUP_FILE}.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "[INFO] Running pg_dump for database..."
pg_dump "$DATABASE_URL" -F p -v > "$BACKUP_FILE"

echo "[INFO] Compressing backup file..."
gzip -f "$BACKUP_FILE"

echo "[SUCCESS] Local backup generated successfully: ${GZIP_FILE}"

# Upload to S3 if bucket is configured
if [ -n "$S3_BUCKET_NAME" ]; then
    echo "[INFO] Uploading backup to S3 bucket '${S3_BUCKET_NAME}'..."
    aws s3 cp "$GZIP_FILE" "s3://${S3_BUCKET_NAME}/database_backups/$(basename "$GZIP_FILE")"
    echo "[SUCCESS] Uploaded to S3."
    
    # Optional: Clean up local compressed file if uploaded to S3
    rm -f "$GZIP_FILE"
fi
