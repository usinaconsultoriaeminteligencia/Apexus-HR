#!/bin/bash
# Simple Postgres backup script.
#
# Usage:
#   backup.sh <backup_dir> <db_name> <db_user> [db_host] [db_port]
#
# Example (with environment variable PGPASSWORD set):
#   export PGPASSWORD=your_db_password
#   ./backup.sh /var/backups mydb postgres db 5432

set -euo pipefail

BACKUP_DIR=${1:-/backups}
DB_NAME=${2:-postgres}
DB_USER=${3:-postgres}
DB_HOST=${4:-localhost}
DB_PORT=${5:-5432}

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILE_NAME="${DB_NAME}_${TIMESTAMP}.dump.gz"

mkdir -p "$BACKUP_DIR"
echo "Creating backup of ${DB_NAME} at ${BACKUP_DIR}/${FILE_NAME}"

# Perform a custom format dump compressed with gzip
pg_dump -Fc -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" | gzip > "${BACKUP_DIR}/${FILE_NAME}"
echo "Backup completed"
